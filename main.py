"""PhotoShare FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.conf.config import settings
from src.routes import auth, comments, photos, ratings, search, transforms, users


@asynccontextmanager
async def lifespan( _: FastAPI ):
	insecure_secret_keys = { "", "change-me", "replace-with-a-long-random-secret",
	                         }

	if not settings.is_development:
		if settings.secret_key in insecure_secret_keys or len( settings.secret_key ) < 32:
			raise RuntimeError( "A secure SECRET_KEY of at least 32 characters "
			                    "must be configured in production", )

	yield


app = FastAPI( title="PhotoShare API",
               version="1.0.0",
               description="REST API for users, photos, tags, comments, ratings, Cloudinary transformations and QR "
                           "codes.",
               lifespan=lifespan, )

app.add_middleware( CORSMiddleware,
                    allow_origins=[ "*" ] if settings.is_development else [ ],
                    allow_credentials=False,
                    allow_methods=[ "*" ],
                    allow_headers=[ "*" ], )

app.include_router( auth.router, prefix="/api/auth", tags=[ "auth" ] )
app.include_router( users.router, prefix="/api/users", tags=[ "users" ] )
app.include_router( search.router, prefix="/api/photos", tags=[ "search" ] )
app.include_router( photos.router, prefix="/api/photos", tags=[ "photos" ] )
app.include_router( comments.router, prefix="/api", tags=[ "comments" ] )
app.include_router( ratings.router, prefix="/api", tags=[ "ratings" ] )
app.include_router( transforms.router, prefix="/api", tags=[ "transforms" ] )


@app.get( "/",
		tags=[ "health" ],
		summary="API status",
		description="Return basic information confirming that the PhotoShare API is running.", )
async def root() -> dict[ str, str ]:
	return { "status": "ok", "application": "PhotoShare API",
			}


@app.get( "/health",
		tags=[ "health" ],
		summary="Health check",
		description="Return a simple health status for monitoring and deployment checks.", )
async def health() -> dict[ str, str ]:
	return { "status": "healthy",
			}
