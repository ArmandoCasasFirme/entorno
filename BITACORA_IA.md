Bitácora de prompts de IA

1. Contexto del proyecto y RF-01

necesito que modifiques y hagas lo siguiente teniendo en cuenta que este proyecto esta pensado en una cafeteria encargada de suministrar de alimentos a los estudiantes de inacap, debido a las filas grandes que se forman. administracion quiere que los clientes puedan armar su pedido desde su propio telefono, elegir una hora de retiro y pasar a buscarlo a la hora acordada. debo construir en django la app web 'cafeteria fiores' a partir de los requerimientos y modelos de datos que me pidan. te voy a adjuntar las cosas que estan dentro del diagrama en otro prompt.

respuesta de la ia:
modelos (categoria, producto, pedido y detallepedido) creados con sus campos respectivos, claves unicas, etc. junto a las medidas de proteccion para evitar eliminar categorias con productos.


2. Requerimientos RF-02

ahroa necesito que hagas las RF-02, las cuales tienen que cumplir con estos parametros:

solo los usuarios autenticados pueden usar la app, que permite iniciar y cerrar sesion.
hay dos roles: cliente y encargado(is_staff). Cada rol debe acceder solo a sus funciones: si un cliente entra a una direccion del encargado, se le debe negar el acceso.
la sesion debe expirar pasados los 30 min.
el menu muestra el usuario conectado y su rol en todo momento.

respuesta de la ia:
Agrego el inicio de sesion y cierre de sesion por POST en accounts/login y accounts/logout.
la pagina requiere autenticacion y deriva al usuario segun el is_staff tal como se le pidio.
realizo los cambios para la expiracion de los 30 min y ahora tambien muestra el nombre y rol del usuario autenticado.