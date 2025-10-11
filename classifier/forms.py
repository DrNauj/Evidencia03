from django import forms
from .models import CustomerPrediction

class CustomerPredictionForm(forms.ModelForm):
    JOB_CHOICES = [
        ('admin.', 'Administrativo'),
        ('blue-collar', 'Trabajador manual'),
        ('entrepreneur', 'Emprendedor'),
        ('housemaid', 'Empleado doméstico'),
        ('management', 'Gerencia'),
        ('retired', 'Jubilado'),
        ('self-employed', 'Autónomo'),
        ('services', 'Servicios'),
        ('student', 'Estudiante'),
        ('technician', 'Técnico'),
        ('unemployed', 'Desempleado'),
        ('unknown', 'Desconocido')
    ]
    
    MARITAL_CHOICES = [
        ('married', 'Casado'),
        ('single', 'Soltero'),
        ('divorced', 'Divorciado')
    ]
    
    EDUCATION_CHOICES = [
        ('primary', 'Primaria'),
        ('secondary', 'Secundaria'),
        ('tertiary', 'Superior'),
        ('unknown', 'Desconocido')
    ]
    
    YES_NO_CHOICES = [
        ('yes', 'Sí'),
        ('no', 'No')
    ]
    
    MONTH_CHOICES = [
        ('jan', 'Enero'), ('feb', 'Febrero'), ('mar', 'Marzo'),
        ('apr', 'Abril'), ('may', 'Mayo'), ('jun', 'Junio'),
        ('jul', 'Julio'), ('aug', 'Agosto'), ('sep', 'Septiembre'),
        ('oct', 'Octubre'), ('nov', 'Noviembre'), ('dec', 'Diciembre')
    ]
    
    CONTACT_CHOICES = [
        ('cellular', 'Celular'),
        ('telephone', 'Teléfono fijo'),
        ('unknown', 'Desconocido')
    ]
    
    POUTCOME_CHOICES = [
        ('failure', 'Fallido'),
        ('success', 'Exitoso'),
        ('other', 'Otro'),
        ('unknown', 'Desconocido')
    ]
    
    # Sobrescribir campos con choices
    job = forms.ChoiceField(choices=JOB_CHOICES)
    marital = forms.ChoiceField(choices=MARITAL_CHOICES)
    education = forms.ChoiceField(choices=EDUCATION_CHOICES)
    default = forms.ChoiceField(choices=YES_NO_CHOICES)
    housing = forms.ChoiceField(choices=YES_NO_CHOICES)
    loan = forms.ChoiceField(choices=YES_NO_CHOICES)
    contact = forms.ChoiceField(choices=CONTACT_CHOICES)
    month = forms.ChoiceField(choices=MONTH_CHOICES)
    poutcome = forms.ChoiceField(choices=POUTCOME_CHOICES)
    
    class Meta:
        model = CustomerPrediction
        fields = ['age', 'job', 'marital', 'education', 'default', 'balance',
                 'housing', 'loan', 'contact', 'day', 'month', 'duration',
                 'campaign', 'pdays', 'previous', 'poutcome']
        labels = {
            'age': 'Edad',
            'job': 'Trabajo',
            'marital': 'Estado Civil',
            'education': 'Educación',
            'default': '¿Tiene impago crediticio?',
            'balance': 'Balance',
            'housing': '¿Tiene préstamo hipotecario?',
            'loan': '¿Tiene préstamo personal?',
            'contact': 'Tipo de contacto',
            'day': 'Día del mes',
            'month': 'Mes',
            'duration': 'Duración (segundos)',
            'campaign': 'Número de contactos',
            'pdays': 'Días desde último contacto',
            'previous': 'Contactos previos',
            'poutcome': 'Resultado campaña anterior'
        }