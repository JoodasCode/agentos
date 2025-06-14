from main import app

# Vercel expects the app to be available as a callable
def handler(request):
    return app(request)

# For Vercel compatibility
application = app 