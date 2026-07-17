<?xml version="1.0" encoding="utf-8"?>
<RESIST version="4.0.0.2475" country_code="NZ" code_year="1992" language="en"
        modeller="Amanda novika" file_date="20 May 2026 10:36:40" project="Fixture Test">
  <Building soil_id="3" importance_category="2">
    <Perimeter length="22" area="30">
      <Point x="0" y="0"/>
      <Point x="6" y="0"/>
      <Point x="6" y="5"/>
      <Point x="0" y="5"/>
    </Perimeter>
    <Storeys num_storeys="2">
      <Storey height="3.6" level="all"/>
    </Storeys>
    <Roof height="1.44" dead_load_id="2"/>
    <Wind region="A"/>
    <LateralResistStructure direction="x" num_components="2">
      <BracedFrame bracing_type="Concentric Tension Only Bracing" bay_length="1.0"
                   num_bays="1" num_br_bays="1" class="SteelTensionConcentricBracedFrame">
        <Braces depth="0.1"/>
      </BracedFrame>
      <CentreOfRigidity x="3" y="2.5"/>
      <Layout><Point x="0" y="0"/><Point x="6" y="0"/></Layout>
    </LateralResistStructure>
    <LateralResistStructure direction="y" num_components="2">
      <BracedFrame bracing_type="Concentric Tension Only Bracing" bay_length="1.0"
                   num_bays="1" num_br_bays="1" class="SteelTensionConcentricBracedFrame">
        <Braces depth="0.1"/>
      </BracedFrame>
      <CentreOfRigidity x="3" y="2.5"/>
      <Layout><Point x="0" y="0"/><Point x="0" y="5"/></Layout>
    </LateralResistStructure>
  </Building>
  <Earthquake zone_factor="0.5"/>
</RESIST>
