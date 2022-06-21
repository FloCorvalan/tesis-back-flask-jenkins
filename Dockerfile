FROM ubuntu:20.04

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt
RUN DEBIAN_FRONTEND=noninteractive TZ=America/Santiago apt-get -y install tzdata
ENV TZ=America/Santiago
RUN ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && dpkg-reconfigure -f noninteractive tzdata

COPY /src /app
COPY .env /app

ENTRYPOINT [ "python3" ]

CMD [ "app.py" ]