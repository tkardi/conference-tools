#!/usr/bin/env python3

# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Volker Mische <volker.mische@gmail.com>

# This script returns the access token in order to upload file to YouTube.
# It's based on the [`oauth_flow.py` example from `python-youtube`](https://github.com/sns-sdks/python-youtube/blob/280d8077c33c9920e0c5c4f9583e64e30b67f892/examples/apis/oauth_flow.py)
#
# It requires a client secret file. It can be obtained from the Google Cloud
# console. The instructions below are based on https://sns-sdks.lkhardy.cn/python-youtube/getting_started/
#
#  1. Go to https://console.cloud.google.com/
#  2. At the top, click on the select menu that lists the projects. It opens a new popup. Click on the top right on "New Project".
#  3. Enter a name, e.g. "FOSS4G upload".
#  4. Click on "Create".
#  5. Click at the top on the project list drop down and select the newly created "FOSS4G upload" project.
#  6. Click under "Quick acccess" on "API & Services".
#  7. Click at the top (second row) on "+ ENABLE APIS AND SERVICES".
#  8. Scroll to "YouTube".
#  9. Click on "YouTube Data API v3".
#  10. Click on the "ENABLE" button.
#  11. Click on "Credentials" on the left navigation menu.
#  12. Click at the top (second row) on "+ CREATE CREDENTIALS" and select "OAuth client ID".
#  13. Click on "CONFIGURE CONSENT SCREEN".
#  14. Select "User Type" the "external option" (internal would be better but I cannot select it) and click on "Create".
#  15. Fill in an "App name", e.g. "FOSS4G video upload" and select a "User support email".
#  16. Also add to "Developer contact information" an email to "Email addresses".
#  17. Click on "SAVE AND CONTINUE".
#  18. Click on "ADD OR REMOVE SCOPES".
#  19. Under "Manually add scoped" add `https://www.googleapis.com/auth/youtube.upload` there. And click on "ADD TO TABLE".
#  20. Then click "UPDATE" at the bottom (I had to scroll down to see it).
#  21. Click on "SAVE AND CONTINUE".
#  22. Add the users you want to give access to, e.g. "volker.mische@gmail.com".
#  23. Click on "SAVE AND CONTINUE".
#  24. Click at the bottom on "BACK TO DASHBOARD".
#  25. Click on "Credentials" on the left navigation menu.
#  26. Click at the top (second row) on "+ CREATE CREDENTIALS" and select "OAuth client ID".
#  27. For "Application type" choose "Desktop app" and select a name, e.g. "Upload script".
#  28. Click on "CREATE".
#  29. Click on "DOWNLOAD JSON" and save it. We'll use that file as input to the `get_token.py` script.

import os, sys

from pyyoutube import Client

SCOPE = [
    "https://www.googleapis.com/auth/youtube.upload",
]


def get_token(client_secret_path):
    """Returns the token.

    The parameter is the path to a client secret file that was downloaded
    """
    cli = Client(client_secret_path=client_secret_path)

    authorize_url, state = cli.get_authorize_url(
        access_type="offline", scope=SCOPE
    )
    print(
        f"Open the following URL. Use the account that should hold the videos (e.g. the FOSS4G account, *not* your personal one):\n{authorize_url}"
    )

    response_uri = input(
        "Paste the URL you were redirected to (it starts with `localhost`):\n"
    )
    # The redirect to localhost may be `http` instead of `https`. If that's the
    # case, replace it with `https`.
    response_uri_https = response_uri.replace("http://", "https://")

    token = cli.generate_access_token(
        authorization_response=response_uri_https
    ).access_token
    return token


def main(argv=None):
    if argv is None:
        argv = sys.argv

    if len(argv) != 2:
        print(f"Usage: {argv[0]} <client-secret-path.json>")
        return 1

    # Without this hack, there is an error message:
    # Warning: Scope has changed from "https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/youtube" to "https://www.googleapis.com/auth/userinfo.profile"
    # See
    # https://stackoverflow.com/questions/51499034/google-oauthlib-scope-has-changed/68167190#68167190
    # for more information.
    os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

    client_secret_path = argv[1]

    token = get_token(client_secret_path)

    print(f"Your token:\n{token}")


if __name__ == "__main__":
    sys.exit(main())
