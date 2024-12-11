FROM python:3.13
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN touch /app/birthdays.db
ENTRYPOINT ["python"]
CMD ["bd_reminder_bot.py"]