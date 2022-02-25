# SoundWaffle (≈ [SoundCloud](https://soundcloud.com/))
### WaffleStudio 19.5 Rookies Toy Project

Website: https://www.soundwaffle.com/
</br>
API Server: https://api.soundwaffle.com/docs/swagger
</br>
Frontend Codebase: https://github.com/wafflestudio19-5/team10-web

[Preview](https://gravel-mambo-b06.notion.site/4ebdbc746415497eb5f0ff9750f58273?v=58bc695658cd4e9db104933deef6768c)

## Common
```
cd ../soundwaffle-server/soundcloud

python3 -m venv ./venv
source venv/bin/activate
pip3 install -r requirements.txt

sudo yum install redis
sudo systemctl start redis-server
```

## Dev
```
python3 manage.py migrate
python3 manage.py rebuild_index
python3 manage.py runserver
```

## Deploy
```
python3 manage.py migrate --settings=soundcloud.settings.prod
python3 manage.py rebuild_index --settings=soundcloud.settings.prod
python3 manage.py check --deploy --settings=soundcloud.settings.prod

gunicorn soundcloud.wsgi --bind 127.0.0.1:8000 --daemon
sudo nginx -t
sudo service nginx restart
```
