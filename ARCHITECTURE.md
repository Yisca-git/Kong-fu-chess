# ארכיטקטורת פרויקט Kong-Fu-Chess

## תיאור כללי
Kong-Fu-Chess הוא משחק שחמט בזמן אמת. הכלים נעים על פי דפוסי תנועת שחמט, אך המהלכים אינם מיידיים — לכל תנועה יש משך זמן פיזי.

---

## מבנה השכבות

הפרויקט מחולק לשכבות עצמאיות. כל שכבה ניתנת לבדיקה בלי השכבות שמעליה.

```
model/          — מצב לוגי בלבד
rules/          — כללי תנועה וחוקיות
engine/         — תיאום שירות-אפליקציה
realtime/       — תנועה לאורך זמן
input/          — תרגום קלט לפקודות
io/             — פרסור והדפסת לוח
view/           — רינדור חזותי
texttests/      — מריץ בדיקות טקסטואליות
```

---

## תיאור השכבות

### model/
**אחריות:** מצב לוגי של הלוח — מיקומים, כלים, צבעים, סוגים, ומצבי מחזור חיים.

**אסור לה:** פיקסלים, קליקים, רינדור, כללי תנועה, או תזמון.

| קובץ | תוכן |
|---|---|
| `position.py` | `Position(row, col)` — value object, `frozen dataclass` |
| `piece.py` | `Piece`, `Color`, `Kind`, `PieceState` |
| `board.py` | `Board` — בעלים של הסידור הלוגי |
| `game_state.py` | מצב כללי של המשחק (עתידי) |

---

### rules/
**אחריות:** גיאומטריית תנועה לכל סוג כלי, ואימות חוקיות מהלך.

**אסור לה:** שינוי Board, זמן חלוף, אנימציה, רינדור, או טיפול בקלט.

| קובץ | תוכן |
|---|---|
| `piece_rules.py` | מחלקת בסיס אבסטרקטית `PieceRules` עם `legal_destinations` |
| `sliding.py` | פונקציית עזר משותפת להחלקה בכיוון |
| `rook_rules.py` | החלקה אופקית ואנכית |
| `bishop_rules.py` | החלקה אלכסונית |
| `queen_rules.py` | שילוב של `RookRules` ו-`BishopRules` |
| `knight_rules.py` | קפיצות L, מתעלם מחוסמים |
| `king_rules.py` | משבצת אחת בכל כיוון |
| `pawn_rules.py` | קדימה אחת, אכילה באלכסון, ללא en passant/promotion |
| `rules_registry.py` | מיפוי `RULES_BY_KIND: dict[Kind, PieceRules]` |
| `move_validation.py` | `MoveValidation(is_valid, reason)` — DTO |
| `rule_engine.py` | `RuleEngine.validate(board, source, destination)` |

---

### engine/
**אחריות:** תיאום שירות-אפליקציה — גבול הפקודות הציבורי.

**אסור לה:** לוגיקת תנועה ספציפית לכלי, מיפוי פיקסלים, רינדור, פירוש טקסט.

| קובץ | תוכן |
|---|---|
| `move_result.py` | `MoveResult(is_accepted, reason)` — DTO |
| `game_snapshot.py` | `GameSnapshot` + `PieceSnapshot` — DTO לקריאה בלבד עבור Renderer |
| `game_engine.py` | `GameEngine` — מתאם בין `RuleEngine`, `RealTimeArbiter`, ו-`Board` |

---

### realtime/
**אחריות:** אובייקטי Motion פעילים, קידום זמן מדומה, פתרון הגעה, ואירועי אכילה.

**אסור לה:** חוקיות שחמט, קליקים, רינדור, או פירוש סקריפט.

| קובץ | תוכן |
|---|---|
| `motion.py` | `Motion` — תנועה בודדת עם `arrival_time` מחושב |
| `real_time_arbiter.py` | `RealTimeArbiter` — מנהל תנועות פעילות וקידום זמן |

---

## החלטות ארכיטקטוניות

### 1. Position כ-frozen dataclass
**החלטה:** `@dataclass(frozen=True)` עם `row` ו-`col`.

**סיבה:** `Position` הוא value object — אמור להיות בלתי ניתן לשינוי. `frozen=True` נותן שוויון, `hash`, וחסימת שינוי אוטומטית, מה שמאפשר שימוש כמפתח ב-`dict`.

---

### 2. Piece כ-dataclass רגיל עם Enum
**החלטה:** `@dataclass` רגיל (לא `frozen`) עם `Color`, `Kind`, `PieceState` כ-`Enum`.

**סיבה:** `cell` ו-`state` משתנים במהלך המשחק, לכן לא `frozen`. `Enum` נותן בטיחות טיפוסים וקריאות. אין לוגיקה בתוך `Piece` — הוא רק נתונים.

**נדחה:** ממשק/מחלקת בסיס לכל סוג כלי — מיותר כי ההבדל בין כלים מתבטא רק ב-`kind`, והלוגיקה שייכת לשכבת `rules`.

---

### 3. PieceRules כ-Strategy Pattern
**החלטה:** מחלקת בסיס אבסטרקטית `PieceRules` עם `legal_destinations(board, piece)`, ומחלקה נפרדת לכל סוג כלי.

**סיבה:** דפוס Strategy מאפשר הוספת סוג כלי חדש בלי לגעת בקוד קיים — רק מחלקה חדשה ושורה ב-`RULES_BY_KIND`.

**נדחה:** `if/elif` ארוך לפי סוג כלי — קשה להרחבה.

---

### 4. sliding.py כקובץ עזר נפרד
**החלטה:** פונקציית `slide` בקובץ נפרד, מיובאת על ידי `RookRules` ו-`BishopRules`.

**סיבה:** עקרון SRP — כל קובץ אחראי לדבר אחד. עקרון DRY — לוגיקת ההחלקה כתובה פעם אחת.

**נדחה:** `_slide` בתוך `rook_rules.py` ומיובאת משם — `RookRules` לא אמור להיות בעלים של לוגיקה משותפת.

---

### 5. MoveValidation ו-MoveResult כ-DTO נפרד
**החלטה:** כל DTO בקובץ משלו.

**סיבה:** שכבות אחרות (כמו `GameEngine`) משתמשות ב-`MoveValidation` — אם היה יושב ב-`rule_engine.py` הן היו צריכות לייבא ממנו רק בשביל ה-DTO, מה שיוצר תלות מיותרת.

---

### 6. Board ללא לוגיקת אכילה
**החלטה:** `Board.move_piece` מניח שהתא היעד פנוי, וזורק חריגה אם תפוס.

**סיבה:** `Board` לא מחליט מי אוכל את מי — זו אחריות `RealTimeArbiter`. הזרימה: `Arbiter` מזהה אכילה → `remove_piece` על הנאכל → `add_piece` על האוכל.

---

### 7. תנועה לוגית נשארת על תא המקור עד הגעה
**החלטה:** כלי נע נשאר לוגית על תא המקור שלו עד שמגיע ליעד.

**סיבה:** שומר על מצב לוח לוגי סמכותי אחד. `print board` דטרמיניסטי — לפני הגעה מציג לוח ישן, אחרי הגעה מציג לוח מעודכן.

---

### 8. חישוב arrival_time בתוך Motion
**החלטה:** `Motion.__post_init__` מחשב `arrival_time = start_time + steps * 1000`.

**סיבה:** `Motion` יודע מקור ויעד — הוא המקום הטבעי לחישוב. שומר את `RealTimeArbiter` נקי מחישובי זמן.

**קבועים:** `CELL_SIZE = 100px`, `PIECE_SPEED = 100px/s` → `1000ms` לכל צעד-תא. תנועה אלכסונית משתמשת ב-`max(|dr|, |dc|)` ולא במרחק אוקלידי.

---

## כללי תנועה — רגלי (Pawn)
- לבן נע שורה אחת למעלה, שחור שורה אחת למטה
- אכילה באלכסון קדימה בלבד
- אין מהלך פתיחה של שתי משבצות
- אין en passant
- אין promotion

---

## תנאי ניצחון
אכילת מלך היריב בפועל — אין שח, מט, או פאט.
