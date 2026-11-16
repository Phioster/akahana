## The places that get a page in the book and the regions that get a name scroll (docs/namen.md,
## approved 2026-11-16). Places are circles round a spot of the world; the two rooms (cave, greenhouse)
## count when you go in. Regions are plain bands of the map, checked in order.
class_name Memories
extends RefCounted

const TEXT_W := 126.0                 # the monk's lines wrap at the paper's edge (PAPER_RIGHT 144 - text x 18)

const REGIONS := [
	{"key": "mitte", "kanji": "赤花の原", "romaji": "Akahana-no-hara"},
	{"key": "kogarashi", "kanji": "木枯らし", "romaji": "Kogarashi"},
	{"key": "norden", "kanji": "雪峰峠", "romaji": "Yukimine-tōge"},
	{"key": "osten", "kanji": "蛍森", "romaji": "Hotarumori"},
	{"key": "sueden", "kanji": "鏡湖", "romaji": "Kagami-ko"},
	{"key": "westen", "kanji": "忘れ里", "romaji": "Wasure-zato"},
]

const PLACES := [
	{"key": "lager", "region": "mitte", "kanji": "焚き火", "romaji": "Takibi", "title": "Lagerfeuer",
		"at": Vector2(1143, 2270), "r": 70.0, "room": "",
		"text": "Hier fing es an. Das Feuer brennt noch."},
	{"key": "schrein", "region": "mitte", "kanji": "赤花神社", "romaji": "Akahana-jinja", "title": "Schrein der roten Blume",
		"at": Vector2(1204, 2103), "r": 50.0, "room": "",
		"text": "Keiner pflegt ihn, doch Mohn liegt vor der Tür."},
	{"key": "ruine", "region": "mitte", "kanji": "古宮", "romaji": "Furumiya", "title": "Alter Schrein",
		"at": Vector2(1129, 1552), "r": 70.0, "room": "",
		"text": "Nur das Tor steht noch, der Mohn wächst hinein."},
	{"key": "bachbruecke", "region": "mitte", "kanji": "小橋", "romaji": "Kobashi", "title": "Kleine Brücke",
		"at": Vector2(1170, 1855), "r": 70.0, "room": "",
		"text": "Drei Bretter über dem Bach. Er zieht leise weiter."},
	{"key": "gluehwuermchen", "region": "sueden", "kanji": "蛍野", "romaji": "Hotaru-no", "title": "Glühwürmchenfeld",
		"at": Vector2(1262, 3150), "r": 70.0, "room": "",
		"text": "Abends steigen Lichter aus dem Gras."},
	{"key": "baeche", "region": "sueden", "kanji": "細流", "romaji": "Seseragi", "title": "Das Plätschern",
		"at": Vector2(1400, 3770), "r": 70.0, "room": "",
		"text": "Überall rinnt Wasser. Man hört es mehr, als man es sieht."},
	{"key": "seesteg", "region": "sueden", "kanji": "灯の桟橋", "romaji": "Hi-no-sanbashi", "title": "Lichtsteg",
		"at": Vector2(1474, 4145), "r": 70.0, "room": "",
		"text": "Am Ende brennt eine Laterne, für wen auch immer."},
	{"key": "seehuette", "region": "sueden", "kanji": "湖畔の小屋", "romaji": "Kohan-no-koya", "title": "Hütte am Seeufer",
		"at": Vector2(1670, 4520), "r": 70.0, "room": "",
		"text": "Licht im Fenster, doch niemand öffnet."},
	{"key": "graeber", "region": "osten", "kanji": "苔の墓", "romaji": "Koke-no-haka", "title": "Moosgräber",
		"at": Vector2(1860, 1750), "r": 70.0, "room": "",
		"text": "Die Namen sind verwittert. Ich grüßte trotzdem."},
	{"key": "steinbruecke", "region": "osten", "kanji": "石橋", "romaji": "Ishibashi", "title": "Steinbrücke",
		"at": Vector2(2240, 1820), "r": 70.0, "room": "",
		"text": "Alte Bögen. Wer sie baute, weiß der Wald nicht mehr."},
	{"key": "waldteich", "region": "osten", "kanji": "大樹の池", "romaji": "Taiju-no-ike", "title": "Teich des großen Baums",
		"at": Vector2(1870, 2550), "r": 70.0, "room": "",
		"text": "Der Baum ist älter als alles hier."},
	{"key": "ritual", "region": "osten", "kanji": "祈りの場", "romaji": "Inori-no-ba", "title": "Ort des Gebets",
		"at": Vector2(2522, 2282), "r": 70.0, "room": "",
		"text": "Steine im Kreis, als warteten sie auf jemanden."},
	{"key": "jizo", "region": "osten", "kanji": "地蔵道", "romaji": "Jizō-michi", "title": "Jizō-Weg",
		"at": Vector2(2290, 2650), "r": 70.0, "room": "",
		"text": "Kleine Jizō am Weg. Jedem nickte ich zu."},
	{"key": "felstor", "region": "norden", "kanji": "岩門", "romaji": "Iwakado", "title": "Felstor",
		"at": Vector2(1174, 1190), "r": 70.0, "room": "",
		"text": "Hinter den Felsen beginnt der Schnee."},
	{"key": "holzfaeller", "region": "norden", "kanji": "木樵の小屋", "romaji": "Kikori-no-koya", "title": "Holzfällerhütte",
		"at": Vector2(1230, 860), "r": 70.0, "room": "",
		"text": "Die Axt steckt im Klotz. Drinnen brennt Licht."},
	{"key": "hoehle", "region": "norden", "kanji": "氷の岩屋", "romaji": "Kōri-no-iwaya", "title": "Eishöhle",
		"at": Vector2(1050, 705), "r": 70.0, "room": "",
		"text": "Ein dunkles Maul im Hang, drinnen ein Schein."},
	{"key": "hoehle_innen", "region": "norden", "kanji": "氷の岩屋", "romaji": "Kōri-no-iwaya", "title": "Eishöhle, innen",
		"at": Vector2.INF, "r": 0.0, "room": "cave",
		"text": "Matte, Kerze, Mohn. Jemand hat hier gewartet."},
	{"key": "schlucht", "region": "norden", "kanji": "雪谷", "romaji": "Yukidani", "title": "Schneeschlucht",
		"at": Vector2(1460, 545), "r": 70.0, "room": "",
		"text": "Der Steg knarrt. Unten ist der Bach gefroren."},
	{"key": "aussicht", "region": "norden", "kanji": "見晴らし", "romaji": "Miharashi", "title": "Aussicht",
		"at": Vector2(1686, 412), "r": 70.0, "room": "",
		"text": "Von hier sieht man fast den ganzen Weg."},
	{"key": "pass", "region": "norden", "kanji": "峠の地蔵", "romaji": "Tōge-no-jizō", "title": "Jizō am Pass",
		"at": Vector2(1370, 125), "r": 70.0, "room": "",
		"text": "Jeder legt einen Stein dazu. Ich auch."},
	{"key": "bergsee", "region": "norden", "kanji": "白滝", "romaji": "Shirataki", "title": "Weißer Wasserfall",
		"at": Vector2(2100, 620), "r": 70.0, "room": "",
		"text": "Der Wasserfall friert nicht, der See nur am Rand."},
	{"key": "einsiedelei", "region": "norden", "kanji": "雪の庵", "romaji": "Yuki-no-iori", "title": "Klause im Schnee",
		"at": Vector2(362, 400), "r": 70.0, "room": "",
		"text": "Eine Glocke, kein Mensch. Die Stille ist anders hier."},
	{"key": "dorfplatz", "region": "westen", "kanji": "井戸端", "romaji": "Idobata", "title": "Brunnenplatz",
		"at": Vector2(520, 2330), "r": 70.0, "room": "",
		"text": "Der Brunnen gibt noch Wasser. Das Dorf schläft."},
	{"key": "gewaechshaus", "region": "westen", "kanji": "硝子室", "romaji": "Garasu-muro", "title": "Glashaus",
		"at": Vector2(680, 2604), "r": 70.0, "room": "",
		"text": "Hinter Glas ist es warm und grün."},
	{"key": "gewaechshaus_innen", "region": "westen", "kanji": "硝子室", "romaji": "Garasu-muro", "title": "Glashaus, innen",
		"at": Vector2.INF, "r": 0.0, "room": "glashaus",
		"text": "Es riecht nach Erde und Regen."},
	{"key": "dorfschrein", "region": "westen", "kanji": "里の社", "romaji": "Sato-no-yashiro", "title": "Dorfschrein",
		"at": Vector2(424, 1860), "r": 70.0, "room": "",
		"text": "Der Bach fließt unter dem Torii hindurch."},
	{"key": "obstwiese", "region": "westen", "kanji": "果樹の原", "romaji": "Kaju-no-hara", "title": "Obstwiese",
		"at": Vector2(635, 1740), "r": 70.0, "room": "",
		"text": "Kaki und Äpfel, keiner erntet. Ich nahm eine."},
	{"key": "muehle", "region": "westen", "kanji": "水車小屋", "romaji": "Suisha-goya", "title": "Wassermühle",
		"at": Vector2(500, 3288), "r": 70.0, "room": "",
		"text": "Das Rad dreht sich, obwohl niemand mehr mahlt."},
	{"key": "bambus", "region": "westen", "kanji": "竹藪", "romaji": "Takeyabu", "title": "Bambushain",
		"at": Vector2(168, 2287), "r": 70.0, "room": "",
		"text": "Ohne Laterne wäre ich nicht hineingegangen."},
	{"key": "fischer", "region": "westen", "kanji": "漁師小屋", "romaji": "Ryōshi-goya", "title": "Fischerhütte",
		"at": Vector2(570, 4110), "r": 70.0, "room": "",
		"text": "Der Steg geht im Zickzack durch die Iris."},
	{"key": "teehaus", "region": "westen", "kanji": "水辺の茶屋", "romaji": "Mizube-no-chaya", "title": "Teehaus am Wasser",
		"at": Vector2(880, 4085), "r": 70.0, "room": "",
		"text": "Ich saß eine Weile und sah aufs Wasser."},
]


static func place(key: String) -> Dictionary:
	for p in PLACES:
		if p.key == key:
			return p
	return {}


static func region(key: String) -> Dictionary:
	for r in REGIONS:
		if r.key == key:
			return r
	return {}


## The nearest place whose circle holds p; the rooms never count out here.
static func place_at(p: Vector2) -> String:
	var best := ""
	var best_d := INF
	for q in PLACES:
		if q.room != "":
			continue
		var d: float = p.distance_to(q.at)
		if d <= q.r and d < best_d:
			best = q.key
			best_d = d
	return best


static func place_in_room(room: String) -> String:
	for q in PLACES:
		if room != "" and q.room == room:
			return q.key
	return ""


## North first (the hermitage is in the snow, not in the village), then the west, the east wood,
## Kogarashi's bare slopes, the south; the poppy field in the middle takes the rest.
static func region_at(p: Vector2) -> String:
	if p.y < 1200.0:
		return "norden"
	if p.x < 900.0:
		return "westen"
	if p.x >= 1700.0 and p.y < 2950.0:
		return "osten"
	if p.y < 1650.0:
		return "kogarashi"
	if p.y >= 2950.0:
		return "sueden"
	return "mitte"


static func wrap_text(text: String) -> PackedStringArray:
	var f := PixelFont.hand()
	var lines := PackedStringArray([""])
	for word in text.split(" ", false):
		var tryit := (lines[-1] + " " + word).strip_edges()
		if lines[-1] == "" or f.get_string_size(tryit, HORIZONTAL_ALIGNMENT_LEFT, -1, PixelFont.HAND_SIZE).x <= TEXT_W:
			lines[-1] = tryit
		else:
			lines.append(word)
	return lines
