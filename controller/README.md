# Controller

## Discogs

To be able to use Discogs as a source for Artist art we need to ask a discogs user for permissions to use their account for image retrieval. For this we need to use the following workflow:

* Is there already a set of user credentials available:
  * /discogs/has-credentials/
* If so: done, if not continue with the next steps
* Redirect the user to a page which asks the user for permission
  * /discogs/get-user-access/
* The user is supplied with a verification code, which is provided to a callback to an API endpoint.

Now the user credentials are stored (and are not asked for next time) and artist art can be retrieved.

## Examples for POST bodies

### /playlist/add

```json
{
    "at_position": 1,
    "start_playing": true,
    "clear_playlist": false,
    "files": [
    {
        "file": "Compilations/Rogue's Gallery_ Pirate Ballads, Sea Songs, & Chanteys/04 Fire Down Below.mp3"
    },
    {
        "file": "Compilations/Rogue's Gallery_ Pirate Ballads, Sea Songs, & Chanteys/27 Pinery Boy.mp3"
    }
    ]
}
```

### /playlist/move

```json
{
    "start_position": 1,
    "end_postion": 2,
    "new_position": 5
}
```

### Structure of project
