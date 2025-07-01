Sub GraphiqueTemperatureResistance()
    Dim ws As Worksheet
    Dim chartObj As ChartObject
    Dim chart As Chart
    Dim lastRow As Long
    Dim timeRange As Range
    Dim tempMesureeRange As Range
    Dim tempConsigneRange As Range
    
    ' Définir la feuille de calcul active
    Set ws = ActiveSheet
    
    ' Trouver la dernière ligne avec des données
    lastRow = ws.Cells(ws.Rows.Count, "A").End(xlUp).Row
    
    ' Définir les plages de données
    Set timeRange = ws.Range("A2:A" & lastRow)
    Set tempMesureeRange = ws.Range("C2:C" & lastRow)
    Set tempConsigneRange = ws.Range("D2:D" & lastRow)
    
    ' Créer le graphique
    Set chartObj = ws.ChartObjects.Add(Left:=100, Top:=50, Width:=600, Height:=400)
    Set chart = chartObj.Chart
    
    ' Configurer le type de graphique (courbes uniquement)
    chart.ChartType = xlXYScatterLinesNoMarkers
    
    ' Ajouter la série Température mesurée
    With chart.SeriesCollection.NewSeries
        .XValues = timeRange
        .Values = tempMesureeRange
        .Name = "Température mesurée"
        .Format.Line.ForeColor.RGB = RGB(255, 0, 0) ' Rouge
    End With
    
    ' Ajouter la série Température consigne
    With chart.SeriesCollection.NewSeries
        .XValues = timeRange
        .Values = tempConsigneRange
        .Name = "Température consigne"
        .Format.Line.ForeColor.RGB = RGB(0, 0, 255) ' Bleu
    End With
    
    ' Configurer l'axe horizontal (temps)
    With chart.Axes(xlCategory)
        .HasTitle = True
        .AxisTitle.Text = "Temps (minutes)"
        .HasMajorGridlines = True
    End With
    
    ' Configurer l'axe vertical (température)
    With chart.Axes(xlValue)
        .HasTitle = True
        .AxisTitle.Text = "Température (°C)"
        .HasMajorGridlines = True
    End With
    
    ' Titre du graphique
    chart.HasTitle = True
    chart.ChartTitle.Text = "Température mesurée vs Température consigne"
    
    ' Ajouter une légende
    chart.HasLegend = True
    chart.Legend.Position = xlLegendPositionBottom
    
End Sub