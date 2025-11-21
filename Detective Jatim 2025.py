#!/usr/bin/env python3
# detektif_jatim_full.py
# Single-file CLI game: Detektif Jatim — splash rainbow, quiz, free, batch, 1-word, hangman, wordle, leaderboard.
# No external libs.

import os
import sys
import random
import re
import csv
import time
from datetime import datetime

# -------------------------
# CONFIG: files & colors
# -------------------------
LEADERBOARD_FILE = "leaderboard.txt"
FEEDBACK_FILE = "feedback.txt"

# ANSI colors for rainbow splash + wordle feedback
COLORS = [
    "\033[38;5;196m",  # red
    "\033[38;5;208m",  # orange
    "\033[38;5;226m",  # yellow
    "\033[38;5;46m",   # green
    "\033[38;5;51m",   # cyan
    "\033[38;5;27m",   # blue
    "\033[38;5;129m",  # purple
]
RESET = "\033[0m"
GREEN = "\033[38;5;40m"   # for wordle correct
YELLOW = "\033[38;5;214m" # for wordle present
GREY = "\033[38;5;240m"   # for wordle absent

# -------------------------
# ASCII Splash (logo)
# -------------------------
ASCII_SPLASH = r"""
 ________    _______  ___________  _______  __   ___  ___________  __     _______  
|"      "\  /"     "|("     _   ")/"     "||/"| /  ")("     _   ")|" \   /"     "| 
(.  ___  :)(: ______) )__/  \\__/(: ______)(: |/   /  )__/  \\__/ ||  | (: ______) 
|: \   ) || \/    |      \\_ /    \/    |  |    __/      \\_ /    |:  |  \/    |   
(| (___\ || // ___)_     |.  |    // ___)_ (// _  \      |.  |    |.  |  // ___)   
|:       :)(:      "|    \:  |   (:      "||: | \  \     \:  |    /\  |\(:  (      
(________/  \_______)     \__|    \_______)(__|  \__)     \__|   (__\_|_)\__/      
                                                                                   
      ___      __  ___________  __     ___      ___                                
     |"  |    /""\("     _   ")|" \   |"  \    /"  |                               
     ||  |   /    \)__/  \\__/ ||  |   \   \  //   |                               
     |:  |  /' /\  \  \\_ /    |:  |   /\\  \/.    |                                
  ___|  /  //  __'  \ |.  |    |.  |  |: \.        |                                
 /  :|_/ )/   /  \\  \\:  |    /\  |\ |.  \    /:  |                                
(_______/(___/    \___)\__|   (__\_|_)|___|\__/|___|                                
"""

def animate_rainbow_shift(text, cycles=36, delay=0.06):
    """Rainbow shifting splash animation (per-line colors shift)."""
    lines = text.split("\n")
    for shift in range(cycles):
        os.system("cls" if os.name == "nt" else "clear")
        shifted = COLORS[shift % len(COLORS):] + COLORS[:shift % len(COLORS)]
        for i, line in enumerate(lines):
            color = shifted[i % len(shifted)]
            print(color + line + RESET)
        time.sleep(delay)
    # final static colored print
    os.system("cls" if os.name == "nt" else "clear")
    for i, line in enumerate(lines):
        print(COLORS[i % len(COLORS)] + line + RESET)
    time.sleep(0.8)
    os.system("cls" if os.name == "nt" else "clear")

def show_splash_screen():
    animate_rainbow_shift(ASCII_SPLASH, cycles=38, delay=0.05)

# -------------------------
# Data: keywords per dialek
# -------------------------
KEYWORDS = {
    "suroboyoan": [
        "rek", "cak", "cok", "jancok", "ndelok", "mangan", "arep",
        "ndisik", "ndang", "opo", "ayo", "le", "tak", "kok", "ndeso",
        "wes", "iso", "cuk", "maceh"
    ],
    "mataraman": [
        "ndak", "opo", "mboten", "kulo", "panjenengan", "arep",
        "ndangu", "nggih", "wes", "durung", "ngene", "yo", "lho",
        "ngantos", "nuwun", "mari"
    ],
    "madura": [
        "ka'", "jhuk", "dhika", "kodhu", "engko", "kaula",
        "beddhi", "nyare", "sapa", "mon", "bhek", "jhah", "melle",
        "ta'", "seppo"
    ]
}

# Dialects list for selection (with 'lainnya')
DIALECTS = ["suroboyoan", "mataraman", "madura", "lainnya"]

# small set of labeled sample sentences for Quiz mode and basic testing
SAMPLES = [
    ("Aku arep mangan rawon rek", "suroboyoan"),
    ("Ndang ojo suwe rek, mangan e wes adhem", "suroboyoan"),
    ("Ayo cak, tak tunggu neng warung", "suroboyoan"),
    ("Nggih kula badhe tindak rumiyin", "mataraman"),
    ("Panjenengan kersa dhahar nopo?", "mataraman"),
    ("Ngene loh carane nggawe sega", "mataraman"),
    ("Sapa ka' nyare?", "madura"),
    ("Engko' badha ka pasar", "madura"),
    ("Kodhu bhâ' potré", "madura"),
    ("Saya mau pergi ke pasar", "lainnya"),
    ("Besok libur kita ke pantai", "lainnya"),
]

# -------------------------
# Utility & model
# -------------------------
def clean_text(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s

def tokenize(s: str):
    s = clean_text(s)
    return s.split()

def score_text(text: str, keywords_map: dict, weight_multi_match: bool = True):
    tokens = tokenize(text)
    scores = {}
    matches = {}
    for label, kwlist in keywords_map.items():
        s = 0
        matched = []
        for kw in kwlist:
            kw_norm = kw.lower().strip()
            if ' ' in kw_norm:
                if kw_norm in ' '.join(tokens):
                    s += 1
                    matched.append(kw_norm)
            else:
                count = sum(1 for t in tokens if t == kw_norm or kw_norm in t)
                if count > 0:
                    matched.extend([kw_norm] * count)
                    s += count if weight_multi_match else 1
        scores[label] = s
        matches[label] = matched
    return scores, matches

def predict(text: str, keywords_map: dict = KEYWORDS):
    scores, matches = score_text(text, keywords_map)
    best_score = max(scores.values()) if scores else 0
    best_labels = [label for label, sc in scores.items() if sc == best_score]
    if best_score == 0:
        return "lainnya", scores, matches
    if len(best_labels) == 1:
        return best_labels[0], scores, matches
    uniques = {label: len(set(matches[label])) for label in best_labels}
    chosen = max(uniques, key=uniques.get)
    top_unique_count = uniques[chosen]
    ties = [l for l, v in uniques.items() if v == top_unique_count]
    if len(ties) == 1:
        return chosen, scores, matches
    return "lainnya", scores, matches

# -------------------------
# Persistence: leaderboard & feedback
# -------------------------
def save_score(name: str, score: int, rounds: int):
    entry = f"{datetime.now().isoformat()},{name},{score},{rounds}\n"
    with open(LEADERBOARD_FILE, "a", encoding='utf-8') as f:
        f.write(entry)

def show_leaderboard(top: int = 10):
    print("\n=== LEADERBOARD ===")
    if not os.path.exists(LEADERBOARD_FILE):
        print("Belum ada skor.")
        return
    rows = []
    with open(LEADERBOARD_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            parts = line.split(",")
            if len(parts) < 4: continue
            ts, name, score, rounds = parts[0], parts[1], parts[2], parts[3]
            try:
                scorev = int(score)
            except:
                scorev = 0
            rows.append((scorev, ts, name, rounds))
    rows.sort(reverse=True, key=lambda x: (x[0], x[1]))
    for i, (scorev, ts, name, rounds) in enumerate(rows[:top], start=1):
        print(f"{i}. {name} — {scorev}/{rounds}  ({ts})")

def save_feedback(text: str, label: str):
    entry = f"{datetime.now().isoformat()}\t{label}\t{text}\n"
    with open(FEEDBACK_FILE, "a", encoding='utf-8') as f:
        f.write(entry)

# -------------------------
# Game modes
# -------------------------
def play_quiz_round(sample):
    text, true_label = sample
    print("\n------------------------------")
    print('Kalimat:')
    print(f'  "{text}"')
    guess = input("Tebakanmu (suroboyoan/mataraman/madura/lainnya): ").strip().lower()
    pred, scores, matches = predict(text)
    print(f"\nModel menjawab: {pred}")
    print("Skor per dialek:", scores)
    print("Kata khas yang terdeteksi per dialek:")
    for l in matches:
        if matches[l]:
            print(f"  - {l}: {sorted(set(matches[l]))}")
    correct = (guess == true_label)
    if correct:
        print("✔ Tebakanmu benar!")
    else:
        print(f"✘ Tebakanmu salah. Jawaban benar: {true_label}")
    if pred == true_label:
        print("Model: prediksi untuk kalimat ini benar.")
    else:
        print("Model: prediksi untuk kalimat ini salah.")
    return 1 if correct else 0

def quiz_mode(samples=None):
    if samples is None:
        samples = SAMPLES[:]
    random.shuffle(samples)
    print("\n=== MODE QUIZ ===")
    n = input(f"Berapa ronde? (max {len(samples)}, default 5): ").strip()
    try:
        n = int(n)
        if n <= 0: raise ValueError
    except:
        n = 5
    n = min(n, len(samples))
    score = 0
    for i in range(n):
        print(f"\nRonde {i+1}/{n}")
        score += play_quiz_round(samples[i])
    print(f"\nSkor akhir: {score}/{n}")
    name = input("Masukkan nama untuk leaderboard (enter untuk skip): ").strip()
    if name:
        save_score(name, score, n)
        show_leaderboard()
    save_feedback_prompt()



# -------------------------
# Minigame: 1-word (single word dialect guess)
# -------------------------
def play_one_word_minigame():
    print("\n╔════════════════════════════╗")
    print("║  MINIGAME: 1-KATA DIALEK  ║")
    print("╚════════════════════════════╝")
    dialect = random.choice(list(KEYWORDS.keys()))
    word = random.choice(KEYWORDS[dialect])
    print("\nTebak dialek dari kata berikut:")
    print(f'  "{word}"')
    hint = input("Butuh hint? (y/n): ").strip().lower()
    if hint == 'y':
        cleaned = clean_text(word)
        length = len(cleaned.replace("'", ""))
        reveal_pos = random.randrange(max(1, length))
        reveal_char = cleaned.replace("'", "")[reveal_pos]
        print(f"Hint: panjang (tanpa apostrof) = {length}, salah satu huruf: '{reveal_char}'")
    guess = input("Tebakanmu (suroboyoan/mataraman/madura/lainnya): ").strip().lower()
    pred, scores, matches = predict(word)
    print(f"\nJawaban benar: {dialect}")
    print(f"Prediksi model (kata saja): {pred}")
    print("Skor:", scores)
    if guess == dialect:
        print("✔ Tebakanmu benar!")
        name = input("Masukkan nama untuk leaderboard (enter=skip): ").strip()
        if name:
            save_score(name, 1, 1)
            show_leaderboard()
    else:
        print("✘ Tebakanmu salah.")
    print("Kata khas yang mempengaruhi:")
    for l, m in matches.items():
        if m:
            print(f" - {l}: {sorted(set(m))}")

# -------------------------
# Hangman (dialek words)
# -------------------------
HANGMANPICS = ['''
  +---+
  |   |
      |
      |
      |
      |
=========''', '''
  +---+
  |   |
  O   |
      |
      |
      |
=========''', '''
  +---+
  |   |
  O   |
  |   |
      |
      |
=========''', '''
  +---+
  |   |
  O   |
 /|   |
      |
      |
=========''', '''
  +---+
  |   |
  O   |
 /|\  |
      |
      |
=========''', '''
  +---+
  |   |
  O   |
 /|\  |
 /    |
      |
=========''', '''
  +---+
  |   |
  O   |
 /|\  |
 / \  |
      |
=========''']

HANGMAN_WORD_POOL = []
for k, lst in KEYWORDS.items():
    for w in lst:
        wn = clean_text(w).replace(" ", "")
        if wn:
            wn = wn.replace("'", "")  # simplify game (remove apostrophes)
            HANGMAN_WORD_POOL.append((wn, k))

def play_hangman():
    print("\n╔════════════════════════════╗")
    print("║        HANGMAN JATIM       ║")
    print("╚════════════════════════════╝")
    secret, dialect = random.choice(HANGMAN_WORD_POOL)
    chosen_word = list(secret)
    blank_list = ["_" for _ in chosen_word]
    update_display = 0
    used_letters = set()
    print("Tebak huruf atau ketik kata penuh jika yakin. Kamu punya 6 kesalahan.")
    print(HANGMANPICS[update_display])
    print(' '.join(blank_list))
    while update_display < len(HANGMANPICS) - 1:
        if blank_list == chosen_word:
            print("\nCONGRATS — KAMU MENANG!")
            break
        guess = input("Masukkan huruf atau tebak kata: ").strip().lower()
        if not guess:
            print("Masukkan sesuatu ya.")
            continue
        if len(guess) > 1:
            if list(guess) == chosen_word:
                blank_list = chosen_word[:]
                print("Tebakan kata benar!")
                break
            else:
                print("Tebakan kata salah.")
                update_display += 1
        else:
            if guess in used_letters:
                print("Huruf sudah dicoba sebelumnya.")
                continue
            used_letters.add(guess)
            if guess in chosen_word:
                for i, ch in enumerate(chosen_word):
                    if ch == guess:
                        blank_list[i] = guess
                print("Betul!")
            else:
                print(f"Tidak ada huruf '{guess}'.")
                update_display += 1
        print(HANGMANPICS[update_display])
        print(' '.join(blank_list))
        print("Used:", ' '.join(sorted(used_letters)))
    if blank_list == chosen_word:
        print(f"Kata: {''.join(chosen_word)}  (dialek: {dialect})")
        pred, scores, matches = predict(''.join(chosen_word))
        print(f"Model prediksi (kata): {pred} | Skor: {scores}")
    else:
        print("\nGAME OVER — kamu kehabisan nyawa.")
        print("Kata yang benar adalah:", ''.join(chosen_word), f"(dialek: {dialect})")

# -------------------------
# Wordle Dialek (colored)
# -------------------------
def choose_dialect():
    os.system("cls" if os.name == "nt" else "clear")
    print("Pilih dialek:")
    for i, d in enumerate(DIALECTS, start=1):
        print(f"{i}. {d.capitalize()}")
    while True:
        try:
            pilih = int(input("\nMasukkan pilihan: "))
            if 1 <= pilih <= len(DIALECTS):
                return DIALECTS[pilih - 1]
            else:
                print("Pilihan tidak valid.")
        except ValueError:
            print("Masukkan angka.")

def color_block(ch, status):
    """Return colored block/char for wordle feedback. status: 'correct','present','absent'"""
    if status == 'correct':
        return GREEN + ch + RESET + " "  # green
    if status == 'present':
        return YELLOW + ch + RESET + " "  # yellow
    return GREY + ch + RESET + " "        # grey

def play_wordle_dialect():
    print("\n╔════════════════════════════╗")
    print("║        WORDLE DIALEK       ║")
    print("╚════════════════════════════╝")
    dialect = choose_dialect()
    if dialect == "lainnya":
        print("\nKamu memilih 'lainnya'. Kamu akan memasukkan kata target.")
        target = input("Masukkan kata target (3–7 huruf): ").lower().strip()
        target = clean_text(target).replace(" ", "").replace("'", "")
        if not (3 <= len(target) <= 7):
            print("Panjang kata tidak valid.")
            return
    else:
        words = [clean_text(w).replace("'", "").replace(" ", "") for w in KEYWORDS.get(dialect, [])]
        words = [w for w in words if 3 <= len(w) <= 7]
        if not words:
            print("Dialek belum memiliki kata 3–7 huruf. Pilih dialek lain.")
            return
        target = random.choice(words)
    attempts = 6
    length = len(target)
    print(f"\nWordle Dialek — {dialect.capitalize()}. Tebak kata {length} huruf. Kamu punya {attempts} percobaan.")
    while attempts > 0:
        guess = input(f"[{attempts} percobaan] Tebakan: ").lower().strip()
        guess = clean_text(guess).replace(" ", "").replace("'", "")
        if len(guess) != length:
            print(f"Kata harus {length} huruf.")
            continue
        # compute feedback (respecting duplicate letters like wordle)
        result = []
        target_list = list(target)
        guess_list = list(guess)
        status = ['absent'] * length
        # first pass: correct positions
        for i in range(length):
            if guess_list[i] == target_list[i]:
                status[i] = 'correct'
                target_list[i] = None  # consume
        # second pass: present (wrong position)
        for i in range(length):
            if status[i] == 'correct':
                continue
            if guess_list[i] in target_list:
                status[i] = 'present'
                # consume first occurrence
                idx = target_list.index(guess_list[i])
                target_list[idx] = None
        # show colored feedback and emoji fallback
        colored = ''.join(color_block(guess_list[i], status[i]) for i in range(length))
        emoji = ''.join('🟩' if status[i]=='correct' else '🟨' if status[i]=='present' else '⬛' for i in range(length))
        print(colored + "   " + emoji)
        if all(s == 'correct' for s in status):
            print("\n🎉 Benar! Kamu menebak dengan tepat.")
            name = input("Masukkan nama untuk leaderboard (enter=skip): ").strip()
            if name:
                save_score(name, 1, 1)
            return
        attempts -= 1
    print(f"\n❌ Gagal! Kata yang benar adalah: {target}")

# -------------------------
# Helpers & Main Menu
# -------------------------
def show_keywords():
    print("\n=== KEYWORDS PER DIALEK (sample) ===")
    for k, v in KEYWORDS.items():
        print(f"- {k}: {', '.join(v[:15])}{'...' if len(v) > 15 else ''}")

def save_feedback_prompt():
    ask = input("Ingin memberi feedback untuk salah/benar model? (y/n): ").strip().lower()
    if ask == 'y':
        text = input("Masukkan kalimat yang tadi: ").strip()
        label = input("Masukkan label yang benar (suroboyoan/mataraman/madura/lainnya): ").strip().lower()
        save_feedback(text, label)
        print("Terima kasih, feedback disimpan.")

def main_menu():
    show_splash_screen()
    while True:
        print("====================================")
        print("  DETEKTIF JAWA TIMUR — terminal")
        print("  (rule-based dialect classifier)")
        print("====================================")
        print("\nPilih mode:")
        print("1. Quiz (tebak dari sample)")
        print("2. Tampilkan keywords (sample)")
        print("3. Tampilkan leaderboard")
        print("4. Minigame: Tebak dialek dari 1 kata")
        print("5. Hangman (kata dialek)")
        print("6. Wordle Dialek")
        print("7. Keluar")
        choice = input("Pilihan [1-9]: ").strip()
        if choice == '1':
            quiz_mode()
        elif choice == '2':
            show_keywords()
        elif choice == '3':
            show_leaderboard()
        elif choice == '4':
            play_one_word_minigame()
        elif choice == '5':
            play_hangman()
        elif choice == '6':
            play_wordle_dialect()
        elif choice == '7':
            print("Sampai jumpa!")
            break
        else:
            print("Pilihan tidak valid.")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nKeluar. Sampai jumpa!")
