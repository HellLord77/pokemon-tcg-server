FROM alpine/git AS data

ARG TAG=latest
RUN git clone https://github.com/PokemonTCG/pokemon-tcg-data.git && \
    cd pokemon-tcg-data && \
    ([[ "$TAG" = "latest" ]] || git checkout ${TAG}) && \
    rm -rf .git

FROM python AS build

RUN apt update && \
    apt install -y default-jdk

WORKDIR /usr/lib/jvm
RUN ln -s default-java temurin

WORKDIR /pylucene
RUN curl https://dlcdn.apache.org/lucene/pylucene/pylucene-9.10.0-src.tar.gz | \
    tar -xz --strip-components=1
RUN cd jcc && \
    JCC_JDK=/usr/lib/jvm/temurin pip wheel --no-cache-dir --no-deps --wheel-dir=../dist . && \
    pip install --no-cache-dir ../dist/*.whl
COPY patch/ /
RUN pip install --no-cache-dir build && \
    PYTHON=python JCC='python -m jcc' NUM_FILES=16 MODERN_PACKAGING=true make

FROM python:slim AS stage

RUN apt update && \
    apt install -y default-jre

WORKDIR /usr/lib/jvm
RUN ln -s default-java temurin

WORKDIR /server

FROM stage AS install

COPY --from=build /pylucene/dist/*.whl .
COPY requirements.txt .
RUN pip install --no-cache-dir --user --find-links=. --requirement=requirements.txt

FROM stage AS prod

COPY --from=install /root/.local /root/.local
COPY src/*.py .

FROM prod AS index

COPY --from=data /git/pokemon-tcg-data data
RUN python init.py

FROM prod

COPY --from=index /server/index index

EXPOSE 8000
ENTRYPOINT ["/root/.local/bin/uvicorn", "main:app"]
CMD ["--host=0.0.0.0"]
