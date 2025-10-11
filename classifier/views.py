from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CustomerPredictionForm
from .models import CustomerPrediction
from .ml.pipeline import create_spark_session, load_model_and_predict
import pandas as pd
from pyspark.sql import Row

def predict_customer(request):
    if request.method == 'POST':
        form = CustomerPredictionForm(request.POST)
        if form.is_valid():
            # Guardar el modelo sin predicción
            customer = form.save(commit=False)
            
            try:
                # Crear sesión Spark
                spark = create_spark_session()
                
                # Convertir datos del formulario a DataFrame de Spark
                data = form.cleaned_data
                pdf = pd.DataFrame([data])
                spark_df = spark.createDataFrame(pdf)
                
                # Realizar predicción
                predictions = load_model_and_predict(spark, spark_df)
                prediction_result = predictions.select("prediction").first()[0]
                
                # Guardar predicción y modelo
                customer.prediction = "yes" if prediction_result == 0.0 else "no"  # Ajustado según el orden de los índices
                customer.save()
                
                messages.success(request, 'Predicción realizada con éxito')
                return redirect('prediction_result', pk=customer.pk)
                
            except Exception as e:
                messages.error(request, f'Error al realizar la predicción: {str(e)}')
                return render(request, 'classifier/predict_form.html', {'form': form})
    else:
        form = CustomerPredictionForm()
    
    return render(request, 'classifier/predict_form.html', {'form': form})

def prediction_result(request, pk):
    prediction = CustomerPrediction.objects.get(pk=pk)
    return render(request, 'classifier/prediction_result.html', {'prediction': prediction})
