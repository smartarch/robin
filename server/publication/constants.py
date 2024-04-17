VENUE_TYPES = [
	("J", "Journal Article"),
	("B", "Whole Book"),
	("C", "Book Chapter"),
	("P", "Conference Proceedings"),
	("M", "Master Thesis"),
	("D", "Doctorate Thesis"),
	("R", "Report"),
	("G", "Magazine"),
	("X", "Miscellaneous"),
	("A", "Archives"),
]

ARTICLE_TYPES = {
	"article": "J",
	"Early Access Articles": "J",
	"book": "B",
	"Book": "B",
	"Book Series": "B",
	"booklet": "X",
	"conference": "P",
	"Conferences": "P",
	"conference-proceeding": "P",
	"Conference Proceeding": "P",
	"proceedings-article": "P",
	"inbook": "X",
	"incollection": "X",
	"inproceedings": "P",
	"Journal-article": "J",
	"journal-article": "J",
	"Journal": "J",
	"Journals": "J",
	"manual": "X",
	"masterthesis": "M",
	"misc": "X",
	"phdthesis": "D",
	"proceedings": "X",
	"techreport": "R",
	"unpublished": "A",
	"other": "X",
	"Magazines": "G",
}

FULL_TEXT_TYPES = [
	("H", "text/html"),
	("P", "application/pdf"),
	("X", "text/xml"),
	("T", "text/plain")
]

FULL_TEXT_STATUS = [
	("E", "Empty"),
	("N", "Not found"),
	("D", "Downloaded"),
	("U", "Uploaded")
]
