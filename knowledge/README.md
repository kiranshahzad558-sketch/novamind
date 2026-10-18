# NovaMind Knowledge Base

Jarvis ki "expert memory" — yahan saved har source ko LLM parhne ke baad
jawab deta hai (retrieval-style: model ko context mein diya jata hai,
dobara training nahi hoti — lekin user ke liye asar wahi hai: expert jawab).

## Structure

```
knowledge/
  loader.py            # sab .md/.txt load karke LLM context banata hai
  sources/
    higgsfield-academy/  # Higgsfield AI Academy — AI video creation course
    wildlife-playbook/   # user's documentary formula (future)
```

## Source add karne ka tareeqa

1. `knowledge/sources/<source-name>/` folder banao.
2. Material `.md` files mein daalo (PDFs ko pehle text mein convert karo).
3. `SOURCES.md` mein likho: kya hai, kahan se aaya, kab update hua.
4. `loader.py` khud sab utha lega — kuch register karne ki zaroorat nahi.

## Higgsfield Academy

Status: course account-wall ke peeche hai. User free account bana kar
lesson PDFs download kare, assistant unhe yahan `.md` mein convert karke
save karega. 7 lessons + homework + certificate track.
