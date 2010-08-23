
from champ2.models import * 

#======================================================
def matrice_value_set_incomplete_count(matrice_value_set):
    
    #check to see that counts match up
    metrics_count = MatriceMetric.objects.all().count()
    values_count = matrice_value_set.values.filter(value__isnull=False).count()
    
    return metrics_count - values_count
     
    
def matrice_value_set_invalid_count(matrice_value_set):
    count = 0
    
    #check to see that each value is between 1 add 4
    for value in matrice_value_set.values.all():
        if value.value != None:
            if value.value > 4 or value.value < 1:
                count = count +1 
            
    return count


#returns number of fields left to complete for a given metric and and value set 
def matrice_program_area_incomplete_count(matrice_program_area, matrice_value_set):
    metrics_count = MatriceMetric.objects.filter(matrice_program_area = matrice_program_area).count()
    values_count = matrice_value_set.values.filter(matrice_metric__matrice_program_area = matrice_program_area).filter(value__isnull=False).count()
    
    return metrics_count - values_count