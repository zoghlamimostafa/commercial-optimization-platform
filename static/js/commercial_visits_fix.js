// Fix for commercial visits page
$(document).ready(function() {
    console.log("Commercial visits fix script loaded");
    
    // Override analyzeVisits function to work with our modified API
    window.analyzeVisits = function() {
        console.log("Override analyzeVisits function called");
        // Récupérer les paramètres
        const dateDebut = $('#dateDebut').val();
        const dateFin = $('#dateFin').val();
        const days = $('#predictionDays').val();
        
        // Validation des dates
        if (new Date(dateDebut) > new Date(dateFin)) {
            Swal.fire({
                icon: 'error',
                title: 'Erreur de dates',
                text: 'La date de début doit être antérieure à la date de fin',
                confirmButtonColor: '#3f51b5'
            });
            return;
        }
        
        // Réinitialiser et afficher les indicateurs de chargement
        $('#statsContainer').hide().empty();
        $('#plotContainer').hide();
        $('#loadingPlot').show();
        $('#predictionsTableContainer').hide();
        $('#loadingPredictions').show();
        $('#exportCsvBtn').prop('disabled', true);
        $('#exportExcelBtn').prop('disabled', true);
        
        // Montrer un toast de chargement
        const loadingToast = toastr.info('Analyse en cours...', 'Patientez', {timeOut: 0});
        
        // Charger le graphique d'analyse
        $.ajax({
            url: '/api/visits_analysis_plot',
            type: 'GET',
            data: {
                date_debut: dateDebut,
                date_fin: dateFin
            },
            success: function(data) {
                $('#loadingPlot').hide();
                
                if (data.error) {
                    toastr.clear(loadingToast);
                    Swal.fire({
                        icon: 'error',
                        title: 'Erreur d\'analyse',
                        text: data.error,
                        confirmButtonColor: '#3f51b5'
                    });
                    return;
                }
                
                // Afficher le graphique
                $('#analysisPlot').attr('src', 'data:image/png;base64,' + data.plot);
                $('#plotContainer').show();
                
                // Charger les prédictions
                $.ajax({
                    url: '/api/predict_visits',
                    type: 'GET',
                    data: {
                        date_debut: dateDebut,
                        date_fin: dateFin,
                        days_to_predict: days
                    },
                    success: function(data) {
                        $('#loadingPredictions').hide();
                        toastr.clear(loadingToast);
                        
                        if (data.error) {
                            Swal.fire({
                                icon: 'error',
                                title: 'Erreur de prédiction',
                                text: data.error,
                                confirmButtonColor: '#3f51b5'
                            });
                            return;
                        }
                        
                        // Display stats
                        const statsContainer = $('#statsContainer');
                        statsContainer.empty();
                        
                        Object.keys(data).forEach(function(commCode) {
                            const pred = data[commCode];
                            const stats = pred.stats;
                            
                            // Carte pour la moyenne
                            statsContainer.append(`
                                <div class="col-md-3">
                                    <div class="stats-card">
                                        <h4>Moyenne visites</h4>
                                        <div class="value">${stats.moyenne_visites_predites.toFixed(1)}</div>
                                        <div>${pred.displayName || 'Donnée simulée'}</div>
                                    </div>
                                </div>
                            `);
                            
                            // Carte pour le max
                            statsContainer.append(`
                                <div class="col-md-3">
                                    <div class="stats-card">
                                        <h4>Maximum visites</h4>
                                        <div class="value">${stats.max_visites_predites}</div>
                                        <div>${pred.displayName || 'Donnée simulée'}</div>
                                    </div>
                                </div>
                            `);
                            
                            // Carte pour le min
                            statsContainer.append(`
                                <div class="col-md-3">
                                    <div class="stats-card">
                                        <h4>Minimum visites</h4>
                                        <div class="value">${stats.min_visites_predites}</div>
                                        <div>${pred.displayName || 'Donnée simulée'}</div>
                                    </div>
                                </div>
                            `);
                            
                            // Carte pour le total
                            statsContainer.append(`
                                <div class="col-md-3">
                                    <div class="stats-card">
                                        <h4>Total visites prédites</h4>
                                        <div class="value">${stats.total_visites_predites}</div>
                                        <div>${pred.displayName || 'Donnée simulée'}</div>
                                    </div>
                                </div>
                            `);
                        });
                        
                        statsContainer.show();
                        
                        // Display prediction table
                        const tableBody = $('#predictionsTable tbody');
                        tableBody.empty();
                        
                        Object.keys(data).forEach(function(commCode) {
                            const pred = data[commCode];
                            const displayName = pred.displayName || 'Donnée simulée';
                            
                            for (let i = 0; i < pred.dates.length && i < 100; i++) {
                                tableBody.append(`
                                    <tr>
                                        <td>${displayName}</td>
                                        <td>${pred.dates[i]}</td>
                                        <td>${parseFloat(pred.predictions[i]).toFixed(1)}</td>
                                        <td>${parseFloat(pred.lower_ci[i]).toFixed(1)}</td>
                                        <td>${parseFloat(pred.upper_ci[i]).toFixed(1)}</td>
                                    </tr>
                                `);
                            }
                        });
                        
                        $('#predictionsTableContainer').show();
                        
                        // Enable export buttons
                        $('#exportCsvBtn').prop('disabled', false);
                        $('#exportExcelBtn').prop('disabled', false);
                        
                        // Store data for export
                        window.predictionsData = data;
                        
                        // Scroll to results
                        $('html, body').animate({
                            scrollTop: $("#statsContainer").offset().top - 20
                        }, 500);
                    },
                    error: function(jqXHR) {
                        $('#loadingPredictions').hide();
                        toastr.clear(loadingToast);
                        Swal.fire({
                            icon: 'error',
                            title: 'Erreur de serveur',
                            text: 'Impossible de générer les prédictions: ' + jqXHR.responseText,
                            confirmButtonColor: '#3f51b5'
                        });
                    }
                });
            },
            error: function(jqXHR) {
                $('#loadingPlot').hide();
                toastr.clear(loadingToast);
                Swal.fire({
                    icon: 'error',
                    title: 'Erreur de serveur',
                    text: 'Impossible de générer l\'analyse: ' + jqXHR.responseText,
                    confirmButtonColor: '#3f51b5'
                });
            }
        });
    };
});
