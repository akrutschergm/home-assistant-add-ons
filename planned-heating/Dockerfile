ARG BUILD_FROM
FROM $BUILD_FROM

# Install requirements for add-on
#RUN apk update && apk upgrade --no-cache && \
RUN apk add python3 py3-pip

# set the working directory in the container
WORKDIR /code

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
#RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# copy the content of the local src directory to the working directory
COPY src/ .

# Copy data for add-on
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]

