var nameColumn = 2;
var scoreColumn = 3;
var lastUpdateColumn = 4;
var IDColumn = 5;
var tableRange = "B:E";
var sheetID = "518408346";

function onEdit(event){
  var editedSheet = event.source;

  if (editedSheet.getSheetId() == sheetID){
    var range = editedSheet.getRange(tableRange);
    range.sort([{ column : scoreColumn, ascending: false }, nameColumn] );
  }
  
}
