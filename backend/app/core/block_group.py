BLOCK_ORDER=[
    "HEADER",
    "SELLER_DETAILS",
    "INVOICE_METADATA",
    "BUYER_DETAILS",    
    "SHIP_TO",
    "ITEM_TABLE",
    "TAX_SUMMARY",
    "BANK_DETAILS",
    "TERMS_AND_CONDITIONS",
    "FOOTER"
]

BLOCK_ANCHORS = {
    "HEADER": [
        "tax invoice",  "original for"
    ],

    "SELLER_DETAILS": [
    "email","pvt", "ltd", "limited", "india", "textiles",
    "mills", "synthetics", "industries", "enterprise",
    "enterprises", "traders", "corporation", "company",
    "co.", "inc", "inc.", "llc", "pvt ltd", "solutions",
    "technologies", "services", "associates", "global",
    "international", "systems","road","pin","post","pincode","email","gstin"
    ],

    "BUYER_DETAILS": [
        "billed to", "bill to", "buyer",
        "receiver", "details of receiver"
    ],

    "SHIP_TO": [
        "ship to", "shipped to", "delivery at",
        "deliver to", "consignee", "details of consignee"
    ],

    "ITEM_TABLE": [
        "description", "hsn", "qty", "quantity",
        "rate", "bags", "total value"
    ],

    "TAX_SUMMARY": [
        "taxable value", "cgst", "sgst",
        "igst", "round off", "invoice total", "total due","subtotal","tax"
    ],

    "BANK_DETAILS": [
        "bank", "account no", "ifsc", "branch"
    ],

    "TERMS_AND_CONDITIONS": [
        "terms & condition", "terms and condition","we assure you"
    ],

    "FOOTER": [
        "authorised signatory", "verified by",
        "prepared by", "for ","thank you for your business"
    ]
}
