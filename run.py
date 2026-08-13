from ventana.config import HOST, PORT
from ventana.web import app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT, reload=False)
