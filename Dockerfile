FROM python:3.12

ENV PYTHONUNBUFFERED 1

WORKDIR /study_bot

COPY requirements.txt /study_bot/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /study_bot/

CMD ["python3", "tutor_bot.py"]


