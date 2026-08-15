<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology" version="3.44">
  <renderer-v2 type="categorizedSymbol" attr="BUILT_FIN" symbollevels="0" forceraster="0" enableorderby="0">
    <categories>
      <category render="true" symbol="0" value="1" type="long" label="Built"/>
      <category render="true" symbol="1" value="0" type="long" label="Planned (future plot)"/>
    </categories>
    <symbols>
      <symbol type="fill" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" enabled="1" locked="0" pass="1">
          <Option type="Map">
            <Option type="QString" name="color" value="0,0,0,0"/>
            <Option type="QString" name="style" value="no"/>
            <Option type="QString" name="outline_color" value="0,0,0,255"/>
            <Option type="QString" name="outline_style" value="solid"/>
            <Option type="QString" name="outline_width" value="0.35"/>
            <Option type="QString" name="outline_width_unit" value="MM"/>
            <Option type="QString" name="joinstyle" value="miter"/>
          </Option>
        </layer>
      </symbol>
      <symbol type="fill" name="1" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" enabled="1" locked="0" pass="0">
          <Option type="Map">
            <Option type="QString" name="color" value="0,0,0,0"/>
            <Option type="QString" name="style" value="no"/>
            <Option type="QString" name="outline_color" value="255,255,255,255"/>
            <Option type="QString" name="outline_style" value="solid"/>
            <Option type="QString" name="outline_width" value="0.35"/>
            <Option type="QString" name="outline_width_unit" value="MM"/>
            <Option type="QString" name="joinstyle" value="miter"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <layerGeometryType>2</layerGeometryType>
</qgis>
