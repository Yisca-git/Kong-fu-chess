# ארכיטקטורת פרויקט Kong-Fu-Chess

## תיאור כללי
Kong-Fu-Chess הוא משחק שחמט בזמן אמת. הכלים נעים על פי דפוסי תנועת שחמט, אך המהלכים אינם מיידיים — לכל תנועה יש משך זמן פיזי. שני השחקנים פועלים במקביל, ללא תורות.

---

## מבנה השכבות

הפרויקט מחולק לשכבות עצמאיות. כל שכבה ניתנת לבדיקה בלי השכבות שמעליה.

```
model/          — מצב לוגי בלבד
rules/          — כללי תנועה וחוקיות
engine/         — תיאום שירות-אפליקציה
realtime/       — תנועה לאורך זמן, קפיצות, ואירועי הגעה
input/          — תרגום קלט לפקודות
text_io/        — פרסור והדפסת לוח
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
| `piece.py` | `Piece`, `Color`, `Kind`, `PieceState` (IDLE, MOVING, AIRBORNE, CAPTURED) |
| `board.py` | `Board` — בעלים של הסידור הלוגי, מבוסס `dict[Position, Piece]` |

---

### input/
**אחריות:** תרגום קלט משתמש לפקודות משחק.

**אסור לה:** חוקיות שחמט, שינוי Board, רינדור, או תזמון.

| קובץ | תוכן |
|---|---|
| `board_mapper.py` | `pixel_to_position(x, y)` — המרת פיקסלים לתאי לוח |
| `controller.py` | `Controller` — ניהול בחירה, `handle_click`, ו-`handle_jump` |

---

### text_io/
**אחריות:** פרסור הגדרת לוח טקסטואלית והדפסת מצב לוח לוגי.

**אסור לה:** כללי תנועה, ביצוע פקודות, רינדור, או לוגיקת בדיקות.

| קובץ | תוכן |
|---|---|
| `board_parser.py` | `parse(text)` — פרסור טקסט לוח ל-`Board` ורשימת `Piece` |
| `board_printer.py` | `print_board(snapshot)` — הדפסת `GameSnapshot` כטקסט |

---

### rules/
**אחריות:** גיאומטריית תנועה לכל סוג כלי, אימות חוקיות מהלך, והתנהגות בהגעה.

**אסור לה:** שינוי Board, זמן חלוף, אנימציה, רינדור, או טיפול בקלט.

| קובץ | תוכן |
|---|---|
| `piece_rules.py` | מחלקת בסיס אבסטרקטית `PieceRules` עם `legal_destinations` ו-`on_arrival` |
| `sliding.py` | פונקציית עזר משותפת להחלקה בכיוון |
| `rook_rules.py` | החלקה אופקית ואנכית |
| `bishop_rules.py` | החלקה אלכסונית |
| `queen_rules.py` | שילוב של `RookRules` ו-`BishopRules` |
| `knight_rules.py` | קפיצות L, מתעלם מחוסמים |
| `king_rules.py` | משבצת אחת בכל כיוון |
| `pawn_rules.py` | קדימה אחת/שתיים מהפתיחה, אכילה באלכסון, הכתרה ב-`on_arrival` |
| `rules_registry.py` | מיפוי `RULES_BY_KIND: dict[Kind, PieceRules]` |
| `move_validation.py` | `MoveValidation(is_valid, reason)` — DTO |
| `rule_engine.py` | `RuleEngine.validate(board, source, destination, moving_origins)` |

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
**אחריות:** אובייקטי Motion ו-Jump פעילים, קידום זמן מדומה, פתרון הגעה, קפיצות, ואירועי אכילה.

**אסור לה:** חוקיות שחמט, קליקים, רינדור, או פירוש סקריפט.

| קובץ | תוכן |
|---|---|
| `motion.py` | `Motion` — תנועה בודדת עם `arrival_time` מחושב |
| `jump.py` | `Jump` — קפיצה במקום עם `land_time` מחושב |
| `real_time_arbiter.py` | `RealTimeArbiter` — מנהל תנועות, קפיצות, וקידום זמן |

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

### 3. Board מבוסס dict[Position, Piece]
**החלטה:** `Board` מחזיק `dict[Position, Piece]` במקום grid דו-ממדי.

**סיבה:** גישה ישירה לפי מיקום ב-O(1), בדיקת ריקות פשוטה, ואין צורך לייצג תאים ריקים. מאפשר לוחות בגדלים שונים בקלות.

---

### 4. PieceRules כ-Strategy Pattern עם on_arrival hook
**החלטה:** מחלקת בסיס אבסטרקטית `PieceRules` עם `legal_destinations(board, piece)` ו-`on_arrival(piece, board_rows)`.

**סיבה:** דפוס Strategy מאפשר הוספת סוג כלי חדש בלי לגעת בקוד קיים — רק מחלקה חדשה ושורה ב-`RULES_BY_KIND`. `on_arrival` הוא hook אופציונלי (ברירת מחדל — לא עושה כלום), כך שרק כלים עם התנהגות מיוחדת בהגעה מממשים אותו.

**נדחה:** `if/elif` ארוך לפי סוג כלי — קשה להרחבה. `PostMoveRules` כמחלקה נפרדת — מיותר כי הלוגיקה שייכת לכלי הספציפי.

---

### 5. sliding.py כקובץ עזר נפרד
**החלטה:** פונקציית `slide` בקובץ נפרד, מיובאת על ידי `RookRules` ו-`BishopRules`.

**סיבה:** עקרון SRP — כל קובץ אחראי לדבר אחד. עקרון DRY — לוגיקת ההחלקה כתובה פעם אחת.

---

### 6. MoveValidation ו-MoveResult כ-DTO נפרד
**החלטה:** כל DTO בקובץ משלו.

**סיבה:** שכבות אחרות משתמשות ב-`MoveValidation` — אם היה יושב ב-`rule_engine.py` הן היו צריכות לייבא ממנו רק בשביל ה-DTO, מה שיוצר תלות מיותרת.

---

### 7. Board ללא לוגיקת אכילה
**החלטה:** `Board` חושף `add_piece`, `remove_piece`, ו-`move_piece` בלבד. `move_piece` מניח שהתא היעד פנוי.

**סיבה:** `Board` לא מחליט מי אוכל את מי — זו אחריות `RealTimeArbiter`. הזרימה: `Arbiter` מזהה אכילה → `remove_piece` על הנאכל → `add_piece` על האוכל.

---

### 8. תנועה מקבילה — חסימה ממוקדת לכלי ספציפי
**החלטה:** `request_move` חוסם רק אם **הכלי הספציפי** כבר בתנועה, לא אם יש תנועה כלשהי על הלוח.

**סיבה:** Kong-Fu-Chess הוא משחק ללא תורות — שני שחקנים זזים במקביל, וכל כלי עצמאי. חסימה גורפת ("יש תנועה כלשהי") סותרת את עיקרון המשחק.

**_BoardWithoutMoving proxy:** `RuleEngine.validate` מקבל `moving_origins: set[Position]` ומשתמש ב-proxy שמסתיר כלים בתנועה מבדיקת נתיב — כי כלי שיצא מתאו לא אמור לחסום נתיב.

---

### 9. תנועה לוגית נשארת על תא המקור עד הגעה
**החלטה:** כלי נע נשאר לוגית על תא המקור שלו עד שמגיע ליעד.

**סיבה:** שומר על מצב לוח לוגי סמכותי אחד. `print board` דטרמיניסטי — לפני הגעה מציג לוח ישן, אחרי הגעה מציג לוח מעודכן.

---

### 10. Jump — כלי airborne נמחק מהלוח הלוגי
**החלטה:** `start_jump` מסיר את הכלי מה-`Board` ומוסיף אותו לרשימת `_jumps` ב-`RealTimeArbiter`. `snapshot()` כולל גם כלים airborne כדי שיופיעו ב-`print board`.

**סיבה:** הפרדה נקייה — הלוח הלוגי מייצג רק כלים "על הקרקע". `RealTimeArbiter` הוא המקום היחיד שיודע על כלים באוויר.

**כלל התנגשות:** תוקף שמגיע לתא של כלי airborne — הקופץ אוכל את התוקף (לא להיפך). אחרי `JUMP_DURATION` הכלי נוחת חזרה אם התא פנוי.

---

### 11. חישוב arrival_time/land_time בתוך Motion/Jump
**החלטה:** `Motion.__post_init__` מחשב `arrival_time`, `Jump.__post_init__` מחשב `land_time`.

**סיבה:** כל אחד מהם יודע את הנתונים הדרושים לחישוב — זה המקום הטבעי. שומר את `RealTimeArbiter` נקי מחישובי זמן.

**קבועים:** `MS_PER_STEP = 1000ms` לכל צעד-תא. `JUMP_DURATION = 1000ms`. תנועה אלכסונית משתמשת ב-`max(|dr|, |dc|)` ולא במרחק אוקלידי.

---

### 12. Controller מכיר רק את GameEngine
**החלטה:** `Controller` מקבל `GameEngine` בבנאי ומשתמש רק בממשקו הציבורי.

**סיבה:** עקרון Dependency Rule — כל שכבה מכירה רק את השכבות שמתחתיה. `Controller` יושב מעל `GameEngine`, לכן אסור לו לגעת ב-`Board` או ב-`RealTimeArbiter` ישירות.

---

### 13. BoardMapper כפונקציה ולא מחלקה
**החלטה:** `pixel_to_position(x, y)` היא פונקציה חופשית, לא מחלקה.

**סיבה:** אין מצב לשמור — המרה פשוטה של `x // CELL_SIZE`, `y // CELL_SIZE`. מחלקה הייתה הפשטת יתר.

---

### 14. BoardParser מחזיר tuple[Board, list[Piece]]
**החלטה:** `parse(text)` מחזיר את שניהם יחד.

**סיבה:** `Board` ו-`Piece` נוצרים יחד ותמיד נדרשים יחד — אין טעם להפריד.

---

## כללי תנועה — רגלי (Pawn)
- לבן נע שורה אחת למעלה (row-1), שחור שורה אחת למטה (row+1)
- צעד כפול משורת הפתיחה (שורה 6 ללבן, שורה 1 לשחור) — רק אם הצעד הראשון פנוי
- אכילה באלכסון קדימה בלבד
- הכתרה למלכה בהגעה לשורה האחרונה — ממומש ב-`on_arrival`
- אין en passant

---

## תנאי ניצחון
אכילת מלך היריב בפועל — אין שח, מט, או פאט.
