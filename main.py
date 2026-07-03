import uvicorn
from misc.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "web.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )