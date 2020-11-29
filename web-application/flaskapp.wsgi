#flaskapp.wsgi
import sys 
sys.path.insert(0, '/var/www/html/kde-project')
  
from flaskapp import app as application