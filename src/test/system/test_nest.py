from nine.cells.nest import load_celltype
CellType = load_celltype('Granule_DeSouza10', '/home/tclose/git/kbrain/xml/cerebellum/ncml/Granule_DeSouza10.xml')
cell = CellType()
cell.describe()