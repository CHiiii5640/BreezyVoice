# Authorized style bank

This directory deliberately contains no audio.  Supply only reference clips for
one speaker for which you have permission, plus an exact UTF-8 transcript for
each clip.  Do not substitute an unrelated voice when a requested clip is absent.

Layout:

```text
data/style_bank/{neutral,happy,sad,excited,gentle,serious,surprised}/{1,2,3}.wav
data/style_bank/{neutral,happy,sad,excited,gentle,serious,surprised}/{1,2,3}.txt
```

The API returns HTTP 422 for an unknown style, invalid intensity, missing WAV,
missing transcript, or blank transcript. Valid references are loaded at startup
and cached for the process lifetime.

Before loading the model, run:

```sh
python scripts/preflight_style_bank.py data/style_bank
```

It emits JSON with all 21 expected entries, decoded WAV format/duration, and
every missing or invalid item. It cannot prove speaker authorization; maintain
that authorization separately.
