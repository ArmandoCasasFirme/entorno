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
3. Requerimientos RF-03

prompt:
necesito una vista de productos para el cliente, que muestre productos disponibles en categorias activas. debe tener busqueda por nombre y filtro por categoria. los precios deben aparecer en pesos chilenos con separador de miles, por ejemplo $1.500. los productos sin stock deben aparecer como agotados y no se deben poder agregar al carrito.

respuesta de la ia:
Se agrega un catálogo con búsqueda y filtro por categorías activas. Los productos no disponibles o de categorías inactivas no aparecen; los productos sin stock se identifican como agotados y la vista también valida el stock al agregarlos al carrito. Los precios se muestran en pesos chilenos con punto como separador de miles.

4. requerimientos RF-06
