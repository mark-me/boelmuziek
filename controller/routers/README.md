# Controller

## Discogs

To be able to use Disgocs as a source for Artist art we need to ask a discogs user for permissions to use their account for image retrieval. For this we need to use the following workflow:

* Is there already a set of user credentials available:
  * /discogs/has-credentials/
* If so: done, if not continue with the next steps
* Redirect the user to a page which asks the user for permission
  * /discogs/get-user-access/
* The user is supplied with a verification code, to accept this
  * /discogs/supply-verification-code/

Now the user credentials are stored (and are not asked for next time) and artist art can be retrieved.