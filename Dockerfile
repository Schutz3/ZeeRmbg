FROM python:3.9

# download more models in https://github.com/danielgatis/rembg/releases/download/v0.0.0/
# on this we were using BiRefNet-massive-TR_DIS5K_TR_TEs-epoch_420.onnx, BiRefNet-general-epoch_244.onnx, isnet-anime.onnx, u2net.onnx  
# copy model to avoid unnecessary download
COPY *.onnx /home/.u2net/

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9033

CMD ["python", "app.py"]