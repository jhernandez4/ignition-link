from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from typing import Annotated
from sqlmodel import select, Session, or_, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from bs4 import BeautifulSoup
import httpx
import json
from ..database import User, PartType, Part, Brand
from ..models import PartLinkResponse 
from ..dependencies import (
    get_session, get_user_from_cookie, encode_model_to_json, get_gemini_client 
)

router = APIRouter(
    prefix="/link",
    tags=["link"],
)

SessionDep = Annotated[Session, Depends(get_session)]
CurrentUserDep = Annotated[User, Depends(get_user_from_cookie)]

@router.get("", response_model=PartLinkResponse)
async def get_data_from_part_page_link(
    session: SessionDep,
    url: str 
):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    # Step 1: Fetch HTML
    try:
        async with httpx.AsyncClient(headers=headers) as client:
            response = await client.get(url)
            response.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(status_code=400, detail="Unable to fetch page.")

    html = response.text

    # Step 2: Use Gemini to extract structured data
    gemini = get_gemini_client()
    prompt = f"""Extract the following fields from this HTML page:
    - Brand name
    - Part name
    - Part number (if any)
    - One image URL (if any)
    - Description

    To expand, the image URL should the link found inside the src attributes of an img element and should
    end in a .jpg, .png or other image file format. Here is the websites url: {url}

    Take note if the src attribute uses relative pathing, so in that case put the root url before the
    src link. For example: "https://conceptzperformance.com" and the relative path "/items/33725/original/3.jpg" should 
    then be "https://conceptzperformance.com/items/33725/original/3.jpg"
    Respond as a JSON object.
    Output should be a plain string, not in a Markdown code block 
    Here is an example of how the output should be structured:

    {{
        "brand": "Borla",
        "part_name": "2017-2021 Honda Civic Type R Cat-Back Exhaust System ATAK",
        "part_number": "140738",
        "image_url": "https://www.borla.com/media/catalog/product/140738/140738-main-1-large.jpg",
        "description": "This is a description that describes the car part"
    }}

    Make sure to  get the correct description from the HTML. The description is likely
    below a title element that says description and may be broken into segments by the br element.
    HTML:
    {html}"""  # limit input for token length if needed

    result = gemini.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt]
    )

    print("JSON response from gemini is: ", result.text)

    try:
        data = result.text.strip("```json").strip("```")  # Clean code block if Gemini returns it
        parsed = json.loads(data)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error parsing AI response.")

    # Step 3: Brand matching
    brand_name = parsed.get("brand", "").strip().lower()
    print("Fetched brand name is: ", brand_name)

    matched_brand = session.exec(
        select(Brand).where(func.lower(Brand.name) == brand_name)
    ).first()

    if not matched_brand:
        raise HTTPException(status_code=404, detail="Brand not found in database.")

    # Very basic matching logic (replace with AI if needed)
    part_types = session.exec(select(PartType)).all()

    part_type_prompt =  f"""
        From the following information about a car part, return the part
        type ID that matchest the best from this list of part types from our database:
        {part_types}

        Your response should be only the part type ID number. Here is the part information:
        {result.text}
    """
    result = gemini.models.generate_content(
        model="gemini-2.0-flash",
        contents=[part_type_prompt]
    )

    # Step 1: Extract the predicted part type ID from Gemini's response
    predicted_part_type_id = result.text.strip()

    print("Gemini predicted part type id: " , result.text)

    # Step 2: Convert the predicted ID from string to int
    try:
        predicted_part_type_id = int(predicted_part_type_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid part type ID returned by Gemini.")

    # Step 3: Query the database for the matched part type using the integer ID
    matched_type = session.exec(select(PartType).where(PartType.id == predicted_part_type_id)).first()

    # Step 4: Error handling if no match is found
    if not matched_type:
        raise HTTPException(status_code=400, detail="Unable to categorize part type.")

    # Continue with the rest of the logic...
    return PartLinkResponse(
        brand_id=matched_brand.id,
        type_id=matched_type.id,
        part_name=parsed.get("part_name"),
        part_number=parsed.get("part_number"),
        image_url=parsed.get("image_url"),
        description=parsed.get("description"),
    )