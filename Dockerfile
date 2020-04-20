FROM python:3.7-alpine
WORKDIR /myapp
COPY . /myapp
RUN apk add libressl-dev
RUN apk add libffi-dev
RUN apk add gcc
RUN apk add musl-dev
RUN apk add python3-dev
RUN pip install -r requirements.txt
EXPOSE 443
CMD ["python", "ebookshop.py"]
