# V1 פיד חדשות

ממשק נוח לצפייה בפיד של V1, עם כפתור רענן שמושך נתונים בזמן אמת.

## מבנה הפרויקט

```
v1-feed-app/
├── api/
│   └── feed.py          ← Python serverless function (scraping V1)
├── public/
│   └── index.html       ← הממשק
├── vercel.json          ← הגדרות Vercel
├── requirements.txt     ← אין תלות חיצונית (stdlib בלבד)
└── README.md
```

## הוראות דפלוי ל-Vercel (חינמי, 5 דקות)

### שלב 1 — GitHub
1. היכנס ל-https://github.com וצור חשבון (אם אין לך)
2. לחץ **New repository** → שם: `v1-feed` → **Create repository**
3. העלה את כל הקבצים (גרור לדפדפן או השתמש בממשק הWeb של GitHub)

### שלב 2 — Vercel
1. היכנס ל-https://vercel.com → **Sign up with GitHub**
2. לחץ **Add New Project** → בחר את ה-repo `v1-feed`
3. לחץ **Deploy** (אין צורך לשנות שום הגדרה)
4. לאחר ~1 דקה תקבל כתובת כמו: `https://v1-feed-xxxx.vercel.app`

### שלב 3 — עדכן את ה-URL בקוד
פתח את `public/index.html`, מצא את השורה:
```
'REPLACE_WITH_YOUR_VERCEL_URL/api/feed'
```
והחלף ב-URL שקיבלת, למשל:
```
'https://v1-feed-xxxx.vercel.app/api/feed'
```
(זה רלוונטי רק לפתיחת הקובץ ישירות מהמחשב — באתר עצמו זה עובד אוטומטית)

## שימוש
- פתח את הכתובת שקיבלת מ-Vercel
- לחץ **רענן** כדי למשוך את הפריטים העדכניים מ-V1
- לחץ על פריט כדי לצפות בסרטון
- סנן לפי קטגוריה עם הכפתורים בראש
