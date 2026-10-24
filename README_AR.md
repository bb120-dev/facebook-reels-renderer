# ربط n8n مع GitHub Actions

1. ضع `render.py` و`image_generator.py` و`scene_prompts.json` في جذر المستودع.
2. ضع `render.yml` داخل `.github/workflows/`.
3. أضف أسرار Cloudflare (`CF_ACCOUNT_ID`, `CF_API_TOKEN`) وأسرار Cloudinary الثلاثة إلى GitHub Actions.
4. اختبر Run workflow يدوياً أولاً (بدون `payload_b64`).
5. في n8n أنشئ Code Node على فرع الفيديو قبل HTTP Request، واجعلها تُخرج `payload_b64` كما في `N8N_CODE.js`.
6. في HTTP Request: POST إلى `https://api.github.com/repos/bb120-dev/facebook-reels-renderer/actions/workflows/render.yml/dispatches`، Authentication: GitHub fine-grained token with Actions write؛ JSON body: `{"ref":"main","inputs":{"payload_b64":"{{ $json.payload_b64 }}"}}`. استخدم اسم الفرع الفعلي إن لم يكن main.
7. استجابة dispatch الناجحة HTTP 204 تعني بدء التشغيل فقط؛ لا تعني اكتمال الفيديو. يجب متابعة حالة GitHub Actions ثم استخراج رابط Cloudinary قبل النشر على Buffer.
8. في `N8N_CODE.js` يوجد كود بناء المدخلات. النص الصوتي أطول من المدة المحددة لن يُقطع؛ مدة الفيديو النهائية قد تتجاوز 45 ثانية.
9. لا ترسل رموز API في المحادثة؛ استخدم Credentials وGitHub Secrets.

ملاحظة: `render.py` يستخدم رسم إطار كامل لكل لقطة؛ قد يكون مكلفاً زمنياً لفيديو 30–45 ثانية على GitHub Actions. إذا تجاوز المهلة، سننتقل إلى حركة FFmpeg بدل Pillow لكل إطار.
