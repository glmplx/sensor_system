Sub GraphiqueConductance()
    Dim ws As Worksheet
    Dim chartObj As ChartObject
    Dim chart As chart
    Dim lastRow As Long
    Dim timeRange As Range
    Dim conductanceRange As Range
    
    ' Définir la feuille de calcul active
    Set ws = ActiveSheet
    
    ' Trouver la dernière ligne avec des données
    lastRow = ws.Cells(ws.Rows.Count, "A").End(xlUp).Row
    
    ' Définir les plages de données
    Set timeRange = ws.Range("A2:A" & lastRow)
    Set conductanceRange = ws.Range("C2:C" & lastRow)
    
    ' Créer le graphique
    Set chartObj = ws.ChartObjects.Add(Left:=100, Top:=50, Width:=600, Height:=400)
    Set chart = chartObj.chart
    
    ' Configurer le type de graphique (nuage de points)
    chart.ChartType = xlXYScatter
    
    ' Ajouter les données
    With chart.SeriesCollection.NewSeries
        .XValues = timeRange
        .Values = conductanceRange
        .Name = "Conductance"
    End With
    
    ' Configurer les axes
    With chart.Axes(xlCategory)
        .HasTitle = True
        .AxisTitle.Text = "Temps (minutes)"
        .HasMajorGridlines = True
    End With
    
    With chart.Axes(xlValue)
        .HasTitle = True
        .AxisTitle.Text = "Conductance (µS)"
        .HasMajorGridlines = True
    End With
    
    ' Titre du graphique
    chart.HasTitle = True
    chart.ChartTitle.Text = "Conductance en fonction du temps"
    
    ' Ajouter une légende
    chart.HasLegend = True
    chart.Legend.Position = xlLegendPositionBottom
    
End Sub
