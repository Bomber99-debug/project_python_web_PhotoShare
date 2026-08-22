"""User profile and administration endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.user import User
from src.repository.users import (count_user_photos,
                                  get_user_by_email,
                                  get_user_by_username,
                                  set_user_active,
                                  set_user_role,
                                  update_user,
                                  )
from src.schemas.user import UserBanResponse, UserPublicProfile, UserResponse, UserRoleUpdate, UserUpdate
from src.services.dependencies import get_current_active_user
from src.services.permissions import require_admin
from src.services.security import hash_password

router = APIRouter()


@router.get( "/me",
             response_model=UserResponse,
             summary="Get current user profile",
             description="Return the profile of the currently authenticated active user.",
             responses={ 401: { "description": "Authentication required or user account is inactive.", },
                         }, )
async def get_me( user: User = Depends( get_current_active_user ) ) -> User:
	return user


@router.put( "/me",
             response_model=UserResponse,
             summary="Update current user profile",
             description=("Update the current user's username, email, password or avatar URL. "
                          "Email addresses and usernames must remain unique."),
             responses={ 400: { "description": "No fields supplied, email already registered or username already "
                                               "taken.",
                                }, 401: { "description": "Authentication required or user account is inactive.", },
                         }, )
async def update_me( data: UserUpdate,
                     db: AsyncSession = Depends( get_db ),
                     user: User = Depends( get_current_active_user ), ) -> User:
	changes = data.model_dump( exclude_unset=True )
	if not changes:
		raise HTTPException( status_code=400, detail="No fields to update" )
	if "email" in changes and changes[ "email" ] != user.email and await get_user_by_email( db, changes[ "email" ] ):
		raise HTTPException( status_code=400, detail="Email already registered" )
	if "username" in changes and changes[ "username" ] != user.username and await get_user_by_username( db,
	                                                                                                    changes[
		                                                                                                    "username"
	                                                                                                    ], ):
		raise HTTPException( status_code=400, detail="Username already taken" )
	if "password" in changes:
		changes[ "password_hash" ] = hash_password( changes.pop( "password" ) )
	user = await update_user( db, user, changes )
	await db.commit()
	return user


@router.get( "/{username}",
             response_model=UserPublicProfile,
             summary="Get public user profile",
             description="Return public profile information including username, avatar, role, registration date and "
                         "number of uploaded photos.",
             responses={ 404: { "description": "User not found.", },
                         }, )
async def public_profile( username: str, db: AsyncSession = Depends( get_db ) ) -> UserPublicProfile:
	user = await get_user_by_username( db, username )
	if user is None:
		raise HTTPException( status_code=404, detail="User not found" )
	return UserPublicProfile( id=user.id,
	                          username=user.username,
	                          avatar_url=user.avatar_url,
	                          role=user.role,
	                          created_at=user.created_at,
	                          uploaded_photos_count=await count_user_photos( db, user.id ), )


@router.patch( "/{user_id}/ban",
               response_model=UserBanResponse,
               summary="Ban a user",
               description=("Deactivate a user account. A banned user cannot log in "
                            "or use authenticated API operations. Administrator role required."),
               responses={
		               401: { "description": "Authentication required or user account is inactive.", },
		               403: { "description": "Administrator role required.", },
		               404: { "description": "User not found.", },
		               }, )
async def ban_user( user_id: int,
                    db: AsyncSession = Depends( get_db ),
                    _: User = Depends( require_admin ), ) -> UserBanResponse:
	user = await set_user_active( db, user_id, False )
	if user is None:
		raise HTTPException( status_code=404, detail="User not found" )
	await db.commit()
	return UserBanResponse( id=user.id, username=user.username, is_active=False, message="User has been banned" )


@router.patch( "/{user_id}/unban",
               response_model=UserBanResponse,
               summary="Unban a user",
               description="Reactivate a banned user account. Administrator role required.",
               responses={
		               401: { "description": "Authentication required or user account is inactive.", },
		               403: { "description": "Administrator role required.", },
		               404: { "description": "User not found.", },
		               }, )
async def unban_user( user_id: int,
                      db: AsyncSession = Depends( get_db ),
                      _: User = Depends( require_admin ), ) -> UserBanResponse:
	user = await set_user_active( db, user_id, True )
	if user is None:
		raise HTTPException( status_code=404, detail="User not found" )
	await db.commit()
	return UserBanResponse( id=user.id, username=user.username, is_active=True, message="User has been unbanned" )


@router.patch( "/{user_id}/role",
		response_model=UserResponse,
		summary="Change user role",
		description=("Assign the user, moderator or admin role to an existing account. "
		             "Administrator role required."),
		responses={
				401: { "description": "Authentication required or user account is inactive.", },
				403: { "description": "Administrator role required.", },
				404: { "description": "User not found.", },
				}, )
async def change_role( user_id: int,
                       data: UserRoleUpdate,
                       db: AsyncSession = Depends( get_db ),
                       _: User = Depends( require_admin ), ) -> User:
	user = await set_user_role( db, user_id, data.role )
	if user is None:
		raise HTTPException( status_code=404, detail="User not found" )
	await db.commit()
	return user
