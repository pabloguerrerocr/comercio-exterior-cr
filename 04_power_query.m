// Power Query (lenguaje M) — ingesta directa desde la API de UN COMTRADE.
//
// COMO USARLO EN EXCEL
//   Datos → Obtener datos → De otras fuentes → Consulta en blanco
//   → Editor avanzado → pegar este bloque → Cerrar y cargar
//
// Esto reemplaza al CSV: la consulta va a la API, arma la tabla y se refresca
// con un botón. Es lo que separa a Excel como herramienta de Excel como archivo.

let
    // ---------------------------------------------------------------- parámetros
    Reporter = 188,                       // Costa Rica (código M49)
    AnioIni  = 2010,
    AnioFin  = 2024,
    Flujos   = {"X", "M"},

    // ---------------------------------------------------------------- catálogo de socios
    // La API de datos NO devuelve los nombres: vienen en null. Hay que unirlos
    // contra el catálogo de referencia, que es otro endpoint.
    RefCrudo  = Json.Document(Web.Contents(
                  "https://comtradeapi.un.org/files/v1/app/reference/partnerAreas.json")),
    RefLista  = RefCrudo[results],
    RefTabla  = Table.FromList(RefLista, Splitter.SplitByNothing(), null, null,
                               ExtraValues.Error),
    RefExpand = Table.ExpandRecordColumn(RefTabla, "Column1",
                  {"PartnerCode", "PartnerDesc", "isGroup"},
                  {"socio_cod", "socio", "es_agregado"}),
    RefTipos  = Table.TransformColumnTypes(RefExpand,
                  {{"socio_cod", Int64.Type}, {"socio", type text},
                   {"es_agregado", type logical}}),

    // ---------------------------------------------------------------- una consulta
    // partnerCode se OMITE a propósito: mandar 'all' devuelve HTTP 400.
    Traer = (anio as number, flujo as text) as table =>
        let
            Resp = Json.Document(Web.Contents(
                     "https://comtradeapi.un.org",
                     [RelativePath = "public/v1/preview/C/A/HS",
                      Query = [reporterCode = Text.From(Reporter),
                               period       = Text.From(anio),
                               cmdCode      = "TOTAL",
                               flowCode     = flujo]])),
            Datos = Resp[data],
            Tabla = Table.FromList(Datos, Splitter.SplitByNothing(), null, null,
                                   ExtraValues.Error),
            Expand = Table.ExpandRecordColumn(Tabla, "Column1",
                       {"refYear", "flowCode", "partnerCode", "primaryValue"},
                       {"anio", "flujo_cod", "socio_cod", "valor_usd"})
        in
            Expand,

    // ---------------------------------------------------------------- todas las combinaciones
    Combos = Table.AddColumn(
               Table.FromList({AnioIni..AnioFin}, Splitter.SplitByNothing(),
                              type table [anio = number]),
               "flujo", each Flujos),
    Expandido = Table.ExpandListColumn(Combos, "flujo"),
    ConDatos  = Table.AddColumn(Expandido, "datos",
                  each Traer([anio], [flujo])),
    Unido     = Table.Combine(ConDatos[datos]),

    // ---------------------------------------------------------------- limpieza
    Tipos = Table.TransformColumnTypes(Unido,
              {{"anio", Int64.Type}, {"socio_cod", Int64.Type},
               {"valor_usd", type number}, {"flujo_cod", type text}}),
    SinNulos = Table.SelectRows(Tipos, each [valor_usd] <> null and [valor_usd] > 0),
    ConFlujo = Table.AddColumn(SinNulos, "flujo",
                 each if [flujo_cod] = "X" then "Exportacion" else "Importacion",
                 type text),
    ConNombre = Table.NestedJoin(ConFlujo, {"socio_cod"}, RefTipos, {"socio_cod"},
                                 "ref", JoinKind.LeftOuter),
    Nombrado  = Table.ExpandTableColumn(ConNombre, "ref",
                  {"socio", "es_agregado"}, {"socio", "es_agregado"}),
    Final = Table.SelectColumns(Nombrado,
              {"anio", "flujo", "socio_cod", "socio", "es_agregado", "valor_usd"})
in
    Final
