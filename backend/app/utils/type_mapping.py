TYPE_MAPPING: dict[str, str] = {
    # Articles
    "Article": "Articles",
    "article": "Articles",
    "article-journal": "Articles",
    "journal-article": "Articles",
    "Journal articles": "Articles",
    # Books & Monographs
    "book": "Books & Monographs",
    "book-chapter": "Books & Monographs",
    "monograph": "Books & Monographs",
    # Conference materials
    "Conference or Workshop Item": "Conference materials",
    "Conference papers": "Conference materials",
    "proceedings-article": "Conference materials",
    "info:eu-repo/semantics/conferenceObject": "Conference materials",
    # Journal Issues & Contributions to periodicals
    "journal-issue": "Journal Issues & Contributions to periodicals",
    "contributionToPeriodical": "Journal Issues & Contributions to periodicals",
    # Datasets
    "dataset": "Datasets",
    "Dataset": "Datasets",
    "info:eu-repo/semantics/other": "Datasets",
    # Preprints
    "Preprints, Working Papers, ...": "Preprints",
    "preprint": "Preprints",

    "workingPaper": "Preprints",
    # Peer review materials
    "peer-review": "Peer review materials",
    "posted-content": "Peer review materials",
    # Other
    "text": "Other",
    "info:eu-repo/semantics/article": "Other",
    "info:eu-repo/semantics/publishedVersion": "Other",
    "other": "Other",
}


def normalize_type(raw_type: str | None) -> str | None:
    if not raw_type:
        return None
    return TYPE_MAPPING.get(raw_type, "Other")
