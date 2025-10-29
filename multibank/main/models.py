from django.db import models

class User_indiv(models.Model):
    # name = models.CharField(max_length=50)
    # total_sum = models.IntegerField()
    # total_free_sum_Vbank = models.IntegerField()
    # total_free_sum_Abank = models.IntegerField()
    # total_free_sum_Sbank = models.IntegerField()
    pass



    def __str__(self):
        return self.name