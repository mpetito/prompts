# Status line timing, 2026-10-13

```
TIMING node shell median=228 min=185 max=469 runs=20
TIMING node direct median=105 min=98 max=138 runs=20
TIMING python3 shell median=405 min=343 max=538 runs=20
TIMING python3 direct median=239 min=217 max=306 runs=20
TIMING python shell median=212 min=192 max=435 runs=20
TIMING python direct median=114 min=107 max=147 runs=20
OUTPUT same
```

Versions:
- Windows-11-10.0.26220-SP0
- node v24.13.0
- python3 Python 3.14.2
- bash C:\Program Files\Git\bin\bash.exe
- statusline.js from a1a99e7e04df16f5adfb65941c98c60144935bac^ (189be66)
- statusline.py from 4f7b053

Outputs:
- node: `'\x1b[36m\uf07c D:/prompts-statusline\x1b[0m\x1b[90m │ \x1b[0m\x1b[34m\uf401 example/prompts\x1b[0m\x1b[90m │ \x1b[0m\x1b[33m\U000f06a9 Opus 5.5\x1b[0m\x1b[90m \uf0e7 high\x1b[0m\x1b[90m │ \x1b[0m\x1b[32m\uf437 43%\x1b[0m'`
- python3: `'\x1b[36m\uf07c D:/prompts-statusline\x1b[0m\x1b[90m │ \x1b[0m\x1b[34m\uf401 example/prompts\x1b[0m\x1b[90m │ \x1b[0m\x1b[33m\U000f06a9 Opus 5.5\x1b[0m\x1b[90m \uf0e7 high\x1b[0m\x1b[90m │ \x1b[0m\x1b[32m\uf437 43%\x1b[0m'`
- python: `'\x1b[36m\uf07c D:/prompts-statusline\x1b[0m\x1b[90m │ \x1b[0m\x1b[34m\uf401 example/prompts\x1b[0m\x1b[90m │ \x1b[0m\x1b[33m\U000f06a9 Opus 5.5\x1b[0m\x1b[90m \uf0e7 high\x1b[0m\x1b[90m │ \x1b[0m\x1b[32m\uf437 43%\x1b[0m'`
