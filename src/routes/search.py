"""Optional photo search and filtering endpoint."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.role import Role
from src.entity.user import User
from src.repository.photos import search_photos as repository_search
from src.schemas.photo import PhotoResponse
from src.services.dependencies import get_optional_current_user
from src.services.tags import normalize_tag_name

router = APIRouter()


@router.get( "/search",
             response_model=list[ PhotoResponse ],
             summary="Search and filter photos",
             description=("Search photos by description keyword or tag and optionally filter by "
                          "minimum rating and date range. Results may be sorted by creation date "
                          "or rating in ascending or descending order. "
                          "Filtering by `user_id` is restricted to moderators and administrators."),
             responses={
		             400: { "description": ("Invalid sort field, sort order, date range or tag."), },
		             403: { "description": "The user_id filter requires moderator or administrator role.", },
		             }, )
async def search_photos( keyword: str | None = None,
                         tag: str | None = None,
                         min_rating: float | None = Query( default=None, ge=1, le=5 ),
                         sort_by: str = "date",
                         order: str = "desc",
                         user_id: int | None = None,
                         date_from: datetime | None = None,
                         date_to: datetime | None = None,
                         db: AsyncSession = Depends( get_db ),
                         current_user: User | None = Depends( get_optional_current_user ), ):
	if sort_by not in { "date", "rating" }:
		raise HTTPException( status_code=400, detail="sort_by must be 'date' or 'rating'" )
	if order not in { "asc", "desc" }:
		raise HTTPException( status_code=400, detail="order must be 'asc' or 'desc'" )
	if date_from and date_to and date_from > date_to:
		raise HTTPException( status_code=400, detail="date_from must not be after date_to" )
	normalized_tag = None
	if tag is not None:
		try:
			normalized_tag = normalize_tag_name( tag )
		except ValueError as exc:
			raise HTTPException( status_code=400, detail=str( exc ) ) from exc
	if user_id is not None and (current_user is None or current_user.role not in { Role.MODERATOR, Role.ADMIN }):
		raise HTTPException( status_code=403, detail="user_id filter requires moderator or admin role" )
	return await repository_search( db,
	                                keyword=keyword,
	                                tag=normalized_tag,
	                                min_rating=min_rating,
	                                sort_by=sort_by,
	                                order=order,
	                                user_id=user_id,
	                                date_from=date_from,
	                                date_to=date_to, )
