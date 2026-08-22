from fastapi import HTTPException


async def test_upload_photo( client, user_headers, create_photo, ):
	photo = await create_photo( client, user_headers, description="My first photo", tag=" Cats ", )

	assert photo[ "description" ] == "My first photo"
	assert photo[ "image_url" ].startswith( "https://example.com/" )
	assert photo[ "public_id" ].startswith( "photoshare/" )
	assert photo[ "tags" ][ 0 ][ "name" ] == "cats"


async def test_upload_rejects_non_image( client, user_headers, ):
	response = await client.post( "/api/photos",
	                              headers=user_headers,
	                              files={ "file": ("document.txt", b"not an image", "text/plain",
	                                               ),
	                                      }, )

	assert response.status_code == 400
	assert "Only jpeg" in response.json()[ "detail" ]


async def test_upload_rejects_more_than_five_tags( client, user_headers, ):
	files = [ ("file", ("photo.jpg", b"fake-image", "image/jpeg",
	                    ),
	           ),
	          ]

	for tag in [ "one", "two", "three", "four", "five", "six",
	             ]:
		files.append( ("tags", (None, tag,
		                        ),
		               ), )

	response = await client.post( "/api/photos", headers=user_headers, files=files, )

	assert response.status_code == 400
	assert response.json()[ "detail" ] == "A photo can have at most 5 tags"


async def test_upload_rejects_empty_tag( client, user_headers, ):
	files = [ ("file", ("photo.jpg", b"fake-image", "image/jpeg",
	                    ),
	           ), ("tags", (None, "   ",
	                        ),
	               ),
	          ]

	response = await client.post( "/api/photos", headers=user_headers, files=files, )

	assert response.status_code == 400
	assert response.json()[ "detail" ] == "Tag cannot be empty"


async def test_upload_cleans_cloudinary_if_database_operation_fails( client,
                                                                     user_headers,
                                                                     mock_cloudinary,
                                                                     monkeypatch, ):
	async def broken_create_photo( *args, **kwargs ):
		raise HTTPException( status_code=500, detail="Database failure", )

	monkeypatch.setattr( "src.routes.photos.create_photo", broken_create_photo, )

	response = await client.post( "/api/photos",
	                              headers=user_headers,
	                              files={ "file": ("photo.jpg", b"fake-image", "image/jpeg",
	                                               ),
	                                      }, )

	assert response.status_code == 500

	assert mock_cloudinary[ "uploaded" ] == [ "photoshare/test-1",
	                                          ]

	assert mock_cloudinary[ "deleted" ] == [ "photoshare/test-1",
	                                         ]


async def test_get_photo( client, user_headers, create_photo, ):
	photo = await create_photo( client, user_headers, )

	response = await client.get( f"/api/photos/{photo[ 'id' ]}", )

	assert response.status_code == 200

	data = response.json()

	assert data[ "id" ] == photo[ "id" ]
	assert data[ "comments" ] == [ ]
	assert data[ "rating_summary" ] is None
	assert data[ "transformed_photos" ] == [ ]


async def test_update_photo_description_and_tags( client, user_headers, create_photo, ):
	photo = await create_photo( client, user_headers, description="Old description", )

	response = await client.put( f"/api/photos/{photo[ 'id' ]}",
	                             headers=user_headers,
	                             json={ "description": "New description", "tags": [ " One ", "TWO", "one",],}, )

	assert response.status_code == 200

	data = response.json()

	assert data[ "description" ] == "New description"

	tag_names = { tag[ "name" ] for tag in data[ "tags" ] }

	assert tag_names == { "one", "two",}


async def test_other_user_cannot_update_or_delete_photo( client, user_headers, other_user_headers, create_photo, ):
	photo = await create_photo( client, user_headers, )

	update = await client.put( f"/api/photos/{photo[ 'id' ]}",
	                           headers=other_user_headers,
	                           json={ "description": "Hacked",}, )

	delete = await client.delete( f"/api/photos/{photo[ 'id' ]}", headers=other_user_headers, )

	assert update.status_code == 403
	assert delete.status_code == 403


async def test_admin_can_update_and_delete_other_users_photo( client,
                                                              user_headers,
                                                              admin_headers,
                                                              create_photo,
                                                              mock_cloudinary, ):
	photo = await create_photo( client, user_headers, )

	update = await client.put( f"/api/photos/{photo[ 'id' ]}",
	                           headers=admin_headers,
	                           json={ "description": "Updated by admin",}, )

	assert update.status_code == 200
	assert update.json()[ "description" ] == "Updated by admin"

	delete = await client.delete( f"/api/photos/{photo[ 'id' ]}", headers=admin_headers, )

	assert delete.status_code == 200
	assert delete.json()[ "message" ] == "Photo deleted successfully"

	assert photo[ "public_id" ] in mock_cloudinary[ "deleted" ]

	missing = await client.get( f"/api/photos/{photo[ 'id' ]}", )

	assert missing.status_code == 404


async def test_photo_not_found( client, user_headers, ):
	get_response = await client.get( "/api/photos/999999", )

	update_response = await client.put( "/api/photos/999999", headers=user_headers, json={ "description": "Nope",
	                                                                                       }, )

	delete_response = await client.delete( "/api/photos/999999", headers=user_headers, )

	assert get_response.status_code == 404
	assert update_response.status_code == 404
	assert delete_response.status_code == 404


async def test_create_and_list_comments( client, user_headers, create_photo, ):
	photo = await create_photo( client, user_headers, )

	create = await client.post( f"/api/photos/{photo[ 'id' ]}/comments",
	                            headers=user_headers,
	                            json={ "text": "  Nice photo!  ",}, )

	assert create.status_code == 201

	comment = create.json()

	assert comment[ "text" ] == "Nice photo!"

	comments = await client.get( f"/api/photos/{photo[ 'id' ]}/comments", )

	assert comments.status_code == 200
	assert len( comments.json() ) == 1
	assert comments.json()[ 0 ][ "id" ] == comment[ "id" ]


async def test_user_can_edit_own_comment( client, user_headers, create_photo, ):
	photo = await create_photo( client, user_headers, )

	create = await client.post( f"/api/photos/{photo[ 'id' ]}/comments",
	                            headers=user_headers,
	                            json={ "text": "Original",}, )

	comment = create.json()

	response = await client.put( f"/api/comments/{comment[ 'id' ]}", headers=user_headers, json={ "text": "Edited",
	                                                                                              }, )

	assert response.status_code == 200
	assert response.json()[ "text" ] == "Edited"

	assert response.json()[ "updated_at" ] >= comment[ "updated_at" ]


async def test_moderator_can_edit_other_users_comment( client, user_headers, moderator, create_photo, ):
	photo = await create_photo( client, user_headers, )

	create = await client.post( f"/api/photos/{photo[ 'id' ]}/comments",
	                            headers=user_headers,
	                            json={ "text": "Original",}, )

	assert create.status_code == 201

	comment = create.json()

	response = await client.put( f"/api/comments/{comment[ 'id' ]}",
	                             headers=moderator[ "headers" ],
	                             json={ "text": "Edited by moderator",}, )

	assert response.status_code == 200
	assert response.json()[ "text" ] == "Edited by moderator"


async def test_admin_can_edit_other_users_comment( client, user_headers, admin_headers, create_photo, ):
	photo = await create_photo( client, user_headers, )

	create = await client.post( f"/api/photos/{photo[ 'id' ]}/comments",
	                            headers=user_headers,
	                            json={ "text": "Original", }, )

	assert create.status_code == 201

	comment = create.json()

	response = await client.put( f"/api/comments/{comment[ 'id' ]}",
	                             headers=admin_headers,
	                             json={ "text": "Edited by admin",
	                                    }, )

	assert response.status_code == 200
	assert response.json()[ "text" ] == "Edited by admin"


async def test_other_user_cannot_edit_comment( client, user_headers, other_user_headers, create_photo, ):
	photo = await create_photo( client, user_headers, )

	create = await client.post( f"/api/photos/{photo[ 'id' ]}/comments",
	                            headers=user_headers,
	                            json={ "text": "Original",
	                                   }, )

	comment = create.json()

	response = await client.put( f"/api/comments/{comment[ 'id' ]}",
	                             headers=other_user_headers,
	                             json={ "text": "Changed",
	                                    }, )

	assert response.status_code == 403


async def test_normal_user_cannot_delete_comment( client, user_headers, create_photo, ):
	photo = await create_photo( client, user_headers, )

	create = await client.post( f"/api/photos/{photo[ 'id' ]}/comments", headers=user_headers, json={ "text":
		                                                                                                  "Comment",
	                                                                                                  }, )

	comment = create.json()

	response = await client.delete( f"/api/comments/{comment[ 'id' ]}", headers=user_headers, )

	assert response.status_code == 403


async def test_moderator_can_delete_comment( client, user_headers, moderator, create_photo, ):
	photo = await create_photo( client, user_headers, )

	create = await client.post( f"/api/photos/{photo[ 'id' ]}/comments",
	                            headers=user_headers,
	                            json={ "text": "Delete me",
	                                   }, )

	comment = create.json()

	response = await client.delete( f"/api/comments/{comment[ 'id' ]}", headers=moderator[ "headers" ], )

	assert response.status_code == 200
	assert response.json()[ "message" ] == "Comment deleted successfully"


async def test_admin_can_delete_comment( client, user_headers, admin_headers, create_photo, ):
	photo = await create_photo( client, user_headers, )

	create = await client.post( f"/api/photos/{photo[ 'id' ]}/comments",
	                            headers=user_headers,
	                            json={ "text": "Delete me",
	                                   }, )

	comment = create.json()

	response = await client.delete( f"/api/comments/{comment[ 'id' ]}", headers=admin_headers, )

	assert response.status_code == 200


async def test_comment_not_found_cases( client, user_headers, admin_headers, ):
	create = await client.post( "/api/photos/999999/comments", headers=user_headers, json={ "text": "No photo",
	                                                                                        }, )

	listing = await client.get( "/api/photos/999999/comments", )

	update = await client.put( "/api/comments/999999", headers=user_headers, json={ "text": "No comment",
	                                                                                }, )

	delete = await client.delete( "/api/comments/999999", headers=admin_headers, )

	assert create.status_code == 404
	assert listing.status_code == 404
	assert update.status_code == 404
	assert delete.status_code == 404
