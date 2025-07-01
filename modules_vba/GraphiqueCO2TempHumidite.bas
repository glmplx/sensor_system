Sub GraphiqueCO2TempHumidite()
    Dim ws As Worksheet
    Dim chartObj As ChartObject
    Dim chart As Chart
    Dim lastRow As Long
    Dim timeRange As Range
    Dim co2Range As Range
    Dim tempRange As Range
    Dim humRange As Range
    
    ' Définir la feuille de calcul active
    Set ws = ActiveSheet
    
    ' Trouver la dernière ligne avec des données
    lastRow = ws.Cells(ws.Rows.Count, "A").End(xlUp).Row
    
    ' Définir les plages de données
    Set timeRange = ws.Range("A2:A" & lastRow)
    Set co2Range = ws.Range("C2:C" & lastRow)
    Set tempRange = ws.Range("D2:D" & lastRow)
    Set humRange = ws.Range("E2:E" & lastRow)
    
    ' Créer le graphique
    Set chartObj = ws.ChartObjects.Add(Left:=100, Top:=50, Width:=700, Height:=450)
    Set chart = chartObj.Chart
    
    ' Configurer le type de graphique (courbes)
    chart.ChartType = xlXYScatterLines
    
    ' Ajouter la série CO2 (axe principal)
    With chart.SeriesCollection.NewSeries
        .XValues = timeRange
        .Values = co2Range
        .Name = "CO2"
        .Format.Line.ForeColor.RGB = RGB(0, 0, 255) ' Bleu
        .AxisGroup = xlPrimary
    End With
    
    ' Ajouter la série Température (axe secondaire)
    With chart.SeriesCollection.NewSeries
        .XValues = timeRange
        .Values = tempRange
        .Name = "Température"
        .Format.Line.ForeColor.RGB = RGB(255, 0, 0) ' Rouge
        .AxisGroup = xlSecondary
    End With
    
    ' Ajouter la série Humidité (axe secondaire)
    With chart.SeriesCollection.NewSeries
        .XValues = timeRange
        .Values = humRange
        .Name = "Humidité"
        .Format.Line.ForeColor.RGB = RGB(0, 255, 0) ' Vert
        .AxisGroup = xlSecondary
    End With
    
    ' Configurer l'axe principal (temps)
    With chart.Axes(xlCategory)
        .HasTitle = True
        .AxisTitle.Text = "Temps (minutes)"
        .HasMajorGridlines = True
    End With
    
    ' Configurer l'axe principal vertical (CO2)
    With chart.Axes(xlValue, xlPrimary)
        .HasTitle = True
        .AxisTitle.Text = "CO2 (ppm)"
        .HasMajorGridlines = True
    End With
    
    ' Configurer l'axe secondaire vertical (Température/Humidité)
    With chart.Axes(xlValue, xlSecondary)
        .HasTitle = True
        .AxisTitle.Text = "Température (°C) / Humidité (%)"
        .HasMajorGridlines = True
    End With
    
    ' Configurer l'axe secondaire horizontal
    With chart.Axes(xlCategory, xlSecondary)
        .HasMajorGridlines = True
    End With
    
    ' Titre du graphique
    chart.HasTitle = True
    chart.ChartTitle.Text = "CO2, Température et Humidité en fonction du temps"
    
    ' Ajouter une légende
    chart.HasLegend = True
    chart.Legend.Position = xlLegendPositionBottom
    
End Sub