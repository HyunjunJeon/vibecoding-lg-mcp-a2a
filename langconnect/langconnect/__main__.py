import uvicorn

uvicorn.run("langconnect.server:APP", host="0.0.0.0", port=8080)
