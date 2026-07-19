# Deploying PizzaCone to Render

This guide will walk you through deploying your PizzaCone Django application to Render.

## Prerequisites

- GitHub account with your PizzaCone repository pushed
- Render account (sign up at https://render.com)
- All changes committed and pushed to GitHub

## Step 1: Create a Render Account

1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account
3. Authorize Render to access your GitHub repositories

## Step 2: Create a PostgreSQL Database

1. In your Render dashboard, click **"New"** → **"PostgreSQL"**
2. Configure:
   - **Name**: `pizzacone-db`
   - **Database**: `pizzacone`
   - **User**: `pizzacone`
   - **Region**: Choose closest to your location
   - **Plan**: Free tier (for testing) or paid for production
3. Click **"Create Database"**
4. Wait for the database to be created (2-3 minutes)
5. Copy the **Internal Database URL** (you'll need this)

## Step 3: Create a Web Service

1. Click **"New"** → **"Web Service"**
2. Connect your GitHub repository:
   - Search for `pizzacone` repository
   - Select it and click **"Connect"**

3. Configure the Web Service:
   - **Name**: `pizzacone` (or your preferred name)
   - **Environment**: `Python 3`
   - **Region**: Same as database for better performance
   - **Branch**: `main`
   - **Build Command**: Leave as default (Render will detect)
   - **Start Command**: `gunicorn pizzacone_project.wsgi:application`
   - **Plan**: Free tier (for testing) or paid for production

4. **Important**: Add Environment Variables before deploying:
   - Click **"Advanced"** at the bottom
   - Click **"Add Environment Variable"** for each:

   ```
   DEBUG = False
   ENVIRONMENT = production
   ALLOWED_HOSTS = your-render-url.onrender.com
   SECURE_SSL_REDIRECT = True
   SESSION_COOKIE_SECURE = True
   CSRF_COOKIE_SECURE = True
   ```

   - Generate a new SECRET_KEY:
     ```bash
     python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
     ```
   - Add as environment variable: `SECRET_KEY = <generated-key>`

   - Add the database URL (from Step 2):
     ```
     DATABASE_URL = <Internal Database URL from PostgreSQL service>
     ```

5. Click **"Create Web Service"**

## Step 4: Monitor Deployment

1. The deploy should start automatically
2. Monitor the logs to watch the build process
3. Look for any errors in the logs
4. Once deployment is complete, you'll see a green checkmark

## Step 5: Verify Your Deployment

1. Click on the URL provided by Render
2. Your site should load successfully
3. If you get errors, check the logs for details

## Step 6: Create a Superuser (First Time Only)

After successful deployment, you need to create an admin user:

1. In Render dashboard, go to your web service
2. Click the **"Shell"** tab (or use the terminal)
3. Run:
   ```bash
   python manage.py createsuperuser
   ```
4. Follow the prompts to create your admin account

## Troubleshooting

### Build Fails
- Check the build logs in Render dashboard
- Ensure all dependencies in `requirements.txt` are compatible with Python 3.12
- Run `pip install -r requirements.txt` locally to verify

### Database Connection Errors
- Verify DATABASE_URL environment variable is set correctly
- Check that the PostgreSQL database is running
- Look for connection timeout errors in logs

### Static Files Not Loading
- Ensure `whitenoise` is installed (it's in requirements.txt)
- WhiteNoise middleware should be in settings.py
- Run `collectstatic` command (done automatically in build.sh)

### 500 Internal Server Error
- Check the logs for detailed error messages
- Ensure SECRET_KEY is set
- Verify all required environment variables are configured
- Run migrations: `python manage.py migrate`

## Useful Commands via Render Shell

Access via Render dashboard → Web Service → Shell:

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Create static files
python manage.py collectstatic

# Check Django setup
python manage.py check --deploy

# Verify uploaded images referenced in DB actually exist on disk
python manage.py verify_media_integrity

# Same check, but fail with non-zero exit code if any files are missing
python manage.py verify_media_integrity --fail-on-missing

# View logs
tail -f logs/django.log
tail -f logs/security.log
```

## Environment Variables Summary

| Variable | Value | Notes |
|----------|-------|-------|
| `DEBUG` | `False` | Always false in production |
| `ENVIRONMENT` | `production` | Triggers production settings |
| `SECRET_KEY` | Generated key | Use secure random key |
| `ALLOWED_HOSTS` | Your Render URL | `your-app.onrender.com` |
| `DATABASE_URL` | PostgreSQL URL | From Render PostgreSQL service |
| `SECURE_SSL_REDIRECT` | `True` | Force HTTPS |
| `SESSION_COOKIE_SECURE` | `True` | HTTPS only cookies |
| `CSRF_COOKIE_SECURE` | `True` | HTTPS only cookies |
| `EMAIL_BACKEND` | `django.core.mail.backends.smtp.EmailBackend` | SMTP backend for production mail |
| `EMAIL_HOST` | `smtp.gmail.com` | Gmail SMTP host |
| `EMAIL_PORT` | `587` | TLS SMTP port |
| `EMAIL_USE_TLS` | `True` | Gmail requires TLS on port 587 |
| `EMAIL_HOST_USER` | your Gmail address | Store in Render dashboard as secret |
| `EMAIL_HOST_PASSWORD` | Gmail app password | Use app password, not account password |
| `DEFAULT_FROM_EMAIL` | same as `EMAIL_HOST_USER` | Sender used by Django mail |

## File Structure for Render

The following files are required for Render deployment:

```
PizzaCone/
├── Procfile                    # Process definition
├── runtime.txt                 # Python version
├── build.sh                    # Build script
├── render.yaml                 # Render configuration
├── requirements.txt            # Python dependencies
├── manage.py
├── pizzacone_project/
│   ├── settings.py             # Database + Render config
│   ├── wsgi.py
│   └── ...
└── ...
```

## Custom Domain (Optional)

1. In Render dashboard, go to your web service
2. Click **"Settings"**
3. Scroll to **"Custom Domain"**
4. Enter your domain name
5. Follow DNS configuration instructions

## Performance Tips

- Use a paid Render plan for production (free tier has limitations)
- Choose database region closest to your users
- Enable auto-scaling if available
- Monitor resource usage in Render dashboard
- Set up error alerts/notifications

## Monitoring & Logs

Render provides several ways to monitor your application:

1. **Logs**: Real-time application logs
2. **Metrics**: CPU, memory, network usage
3. **Alerts**: Set up notifications for errors
4. **Analytics**: View traffic and performance

Access these in your Render dashboard under the service.

## Updating Your Application

To update your deployed app:

1. Make changes locally
2. Test with `python manage.py check --deploy`
3. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```
4. Render automatically redeploys when changes are pushed to `main` branch

## Security Checklist

Before going live:

- [ ] Set DEBUG = False
- [ ] Generate a strong SECRET_KEY
- [ ] Configure ALLOWED_HOSTS
- [ ] Use HTTPS (automatic with Render)
- [ ] Set SECURE_SSL_REDIRECT = True
- [ ] Set secure cookie flags to True
- [ ] Run `python manage.py check --deploy`
- [ ] Review SECURITY.md for security best practices
- [ ] Set up admin password
- [ ] Configure email settings if needed
- [ ] Set up backups for database

## Support & Resources

- [Render Documentation](https://render.com/docs)
- [Django Deployment Guide](https://docs.djangoproject.com/en/6.0/howto/deployment/)
- [Render + Django Guide](https://render.com/docs/deploy-django)
- [WhiteNoise Documentation](http://whitenoise.evans.io/)

## Next Steps

After successful deployment:

1. Monitor application for errors
2. Set up automated backups
3. Configure custom domain
4. Set up monitoring/alerts
5. Document your deployment process
6. Plan for scaling if needed

---

**Need help?** Check the Render logs in the dashboard or contact Render support.
