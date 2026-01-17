from app.core.block_group import BLOCK_ORDER, BLOCK_ANCHORS

def group_invoice_blocks(lines):
    """Group lines into blocks
      based on predefined anchors."""
    
    #initialise the output structure
    blocks={} 
    for block in BLOCK_ORDER:
        blocks[block]=[] #list of lines in that block
    
    current_block_index=0
    current_block=BLOCK_ORDER[current_block_index]

    for line in lines:
        text=line['text'].lower()

        #check only forwward blocks because we are currently in the block and we never go backwards
        for next_block_index in range(current_block_index+1,len(BLOCK_ORDER)):
            next_block=BLOCK_ORDER[next_block_index]
            anchors=BLOCK_ANCHORS.get(next_block,[])
            if matches_anchor(text,next_block):
                #move to next block
                current_block_index=next_block_index
                current_block=next_block
                break
        blocks[current_block].append(line)
    return blocks

def matches_anchor(text:str,block:str)->bool:
    text=text.lower()
    anchors=BLOCK_ANCHORS.get(block,[])
    for anchor in anchors:
        if anchor in text:
            return True
    return False

#note: blocks is a dict with block names as keys and list of lines as values