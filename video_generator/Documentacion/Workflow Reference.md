##### PASO 1: Research producto (Carol)

* Ver datos ventas + kalodata para elegir productos
* Rellenar sheet Selección de productos:

https://docs.google.com/spreadsheets/d/18b5aQZUby4JHYpnrlZPyisC-aW21z44VKxFJk\_3dviQ/edit?gid=0#gid=0

**TIEMPO ESTIMADO: 30m por producto**
**¿Cuándo? 1 vez por semana / cada 15 días.**


##### PASO 2: Generar product info (Sara)

* Generar con GPT:

>> Deal math
>> Scripts audio
>> Seo 
>> Hastags
>> Text Overlay

* Grabar audios y guardar en la carpeta de producto.
* Rellenar sheet: Guia producción manual

https://docs.google.com/spreadsheets/d/1lecht9yFZqExwIEicFA8yp3fjvCB\_vOHcuDmr852MZk/edit?gid=0#gid=0

**TIEMPO ESTIMADO: 30m por producto**
**¿Cuándo? 1 vez por semana / cada 15 días.**


##### PASO 3: Generar videos IA (Mar)

* Preparación:

>> Ver videos virales del producto 
>> Sacar clips de referencia

* Generar videos 

>> brolls
>> hooks

* Guardar en las carpetas con nomenclatura correcta

**TIEMPO ESTIMADO: 1h 30m por producto**
**¿Cuándo? 1 vez por semana / cada 15 días.**


##### PASO 4: Generar Videos.(Sara + Autotok)

Definir cuantos videos por cuenta / producto y ejecutar.


Cuenta LOTOPDEVICKY (60 videos)

python main.py --producto aceite\_oregano --cuenta lotopdevicky --batch 15
python main.py --producto botella\_bottle --cuenta lotopdevicky --batch 10
python main.py --producto anillo\_simson --cuenta lotopdevicky --batch 10
python main.py --producto arrancador\_coche --cuenta lotopdevicky --batch 10
python main.py --producto melatonina --cuenta lotopdevicky --batch 15


Cuenta ofertastrendy (60 videos)

python main.py --producto aceite\_oregano --cuenta ofertastrendy20 --batch 15
python main.py --producto botella\_bottle --cuenta ofertastrendy20 --batch 10
python main.py --producto anillo\_simson --cuenta ofertastrendy20 --batch 10
python main.py --producto arrancador\_coche --cuenta ofertastrendy20 --batch 10
python main.py --producto melatonina --cuenta ofertastrendy20 --batch 15

**TIEMPO ESTIMADO: 30m / 100 videos** 
**¿Cuándo? 1 vez por semana / cada 15 días.**


##### PASO 5: Generar calendario de publicaciones (Sara + Autotok)

Comprobar cuántos días podemos programar según las reglas de repetición establecidas.

python programador.py --preview --dias  10
python programador.py --generar-calendario --dias 10


**TIEMPO ESTIMADO: 1m**
**¿Cuando? Depende de número de videos disponibles.**


##### PASO 6: Upload borradores + SEO Tags (Sara)

Subir cómo borrador los videos generados y añadir los textos SEO y las tags.

OJO: Aquí tenemos una restricción, Tiktok no permite subir más de 30 borradores por cuenta de manera que sólo puedo ir subiendo los videos en lotes de 30. Por confirmar: Si cuando se programan salen de borrador y se pueden subir nuevos. 

**TIEMPO ESTIMADO: 1h 30 productos**
**¿Cuando? Al principio cada 3 días, cuando estemos a máxima producción diario.** 


##### PASO 7: Programar (Carol)

* Abrir calendario de publicación
* Abrir Tiktok Studio
* Revisar video en borrador
	>> Esta ok? Programar fecha y hora de publicación según hoja y marcar programado en la hoja.
	>> No esta ok? Marcar cómo descartado en la hoja y añadir comentario.

Repetir para los 30 borradores.

**TIEMPO ESTIMADO: 1h 30 productos**
**¿Cuando? Al principio cada 3 días, cuando estemos a máxima producción diario.**

































