from ..app_models import db

# URL for connecting to the application. first is localhost, second is for connecting to heroku
BASE_URL = 'http://127.0.0.1:5000' # for local host

# email url for localhost
# EMAIL_BASE_URL = 'http://127.0.0.1:3000' 

# email config for heroku
EMAIL_BASE_URL = 'https://weconnect-api-app.herokuapp.com'
# BASE_URL = 'https://weconnect-api-app.herokuapp.com' #for heroku application